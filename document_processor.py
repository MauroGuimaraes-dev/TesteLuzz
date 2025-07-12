import os
import logging
import io
import json
from openai import OpenAI
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, api_key: str, model: str, prompts: dict):
        if not api_key:
            raise ValueError("A chave API não pode ser vazia.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompts = prompts
        logger.info(f"DocumentProcessor inicializado com o modelo: {self.model}")

    def _extract_text_from_pdf(self, file_stream) -> str:
        try:
            reader = PdfReader(file_stream)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}")
            return ""

    def _extract_text_from_image(self, file_stream) -> str:
        try:
            image = Image.open(file_stream)
            text = pytesseract.image_to_string(image, lang='por')
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto da imagem: {e}")
            return ""

    def _get_structured_data_from_ai(self, document_text: str) -> dict:
        if not document_text.strip():
            return {"products": []}

        # --- MUDANÇA CRÍTICA: ESTRUTURA DE PROMPT MAIS ROBUSTA ---
        # Usamos o 'system' para dar o contexto e as regras mais importantes.
        system_prompt = f"""
        Você é um assistente de extração de dados altamente preciso. Sua única função é analisar o texto de um documento e retornar um objeto JSON.
        
        REGRAS OBRIGATÓRIAS:
        1.  Sua resposta DEVE ser APENAS um objeto JSON válido.
        2.  NÃO inclua NENHUM texto explicativo, comentários, ou a palavra "json" antes ou depois do objeto JSON.
        3.  O objeto JSON DEVE ter uma única chave principal: "produtos".
        4.  O valor de "produtos" DEVE ser uma lista de objetos.
        5.  Cada objeto na lista representa um produto e DEVE conter as chaves: "codigo", "referencia", "descricao", "quantidade", "valor_unitario".
        6.  Se um campo não for encontrado no texto, seu valor no JSON DEVE ser `null`.
        7.  Campos de quantidade e valor DEVEM ser números (int ou float), sem símbolos de moeda ou formatação.
        8.  Se NENHUM produto for encontrado no texto, você DEVE retornar exatamente: `{{"products": []}}`
        """
        
        # O 'user' prompt agora é mais direto, focando na tarefa específica.
        user_prompt = f"""
        Analise o texto abaixo e extraia os dados dos produtos, seguindo estritamente as regras fornecidas.

        Texto para análise:
        ---
        {document_text}
        ---
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0 # Temperatura zero para máxima precisão e menos criatividade
            )
            
            response_content = response.choices[0].message.content
            
            try:
                json_response = json.loads(response_content)
                if not isinstance(json_response, dict):
                    logger.warning(f"Resposta da IA não é um dicionário: {response_content}")
                    return {}
            except json.JSONDecodeError:
                logger.error(f"Falha ao decodificar JSON da IA. Resposta recebida: {response_content}")
                return {}

            return json_response

        except Exception as e:
            logger.error(f"Erro na chamada da API da OpenAI: {e}")
            raise

    def process_documents(self, filepaths: list) -> dict:
        all_products = []
        processed_files_count = 0
        
        for filepath in filepaths:
            try:
                with open(filepath, 'rb') as f:
                    file_stream = io.BytesIO(f.read())
                    
                    if filepath.lower().endswith('.pdf'):
                        text = self._extract_text_from_pdf(file_stream)
                    elif filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
                        text = self._extract_text_from_image(file_stream)
                    else:
                        logger.warning(f"Formato de arquivo não suportado: {filepath}")
                        continue

                if text:
                    structured_data = self._get_structured_data_from_ai(text)
                    
                    if structured_data and isinstance(structured_data.get('products'), list):
                        for product in structured_data['products']:
                            if product and product.get('descricao'):
                                product['fonte'] = os.path.basename(filepath)
                                all_products.append(product)
                    else:
                        logger.warning(f"Nenhum produto válido encontrado ou formato de resposta incorreto para o arquivo {os.path.basename(filepath)}")

                processed_files_count += 1
                
            except Exception as e:
                logger.error(f"Falha ao processar o arquivo {os.path.basename(filepath)}: {e}")
                continue

        if not all_products:
            return None

        consolidated = {}
        for prod in all_products:
            key = (prod.get('codigo', '').strip() or prod.get('referencia', '').strip() or prod.get('descricao', '').strip()).lower()
            if not key:
                continue

            if key not in consolidated:
                consolidated[key] = prod.copy()
                consolidated[key]['quantidade'] = float(prod.get('quantidade', 0) or 0)
                consolidated[key]['valor_unitario'] = float(prod.get('valor_unitario', 0) or 0)
            else:
                consolidated[key]['quantidade'] += float(prod.get('quantidade', 0) or 0)

        final_products = list(consolidated.values())
        
        total_value = 0
        for prod in final_products:
            prod['valor_total'] = prod['quantidade'] * prod['valor_unitario']
            total_value += prod['valor_total']

        html_table = "<table class='table table-striped table-bordered'><thead><tr><th>Código</th><th>Referência</th><th>Descrição</th><th>Qtd.</th><th>Valor Unit.</th><th>Valor Total</th><th>Fonte</th></tr></thead><tbody>"
        for prod in sorted(final_products, key=lambda p: p.get('descricao', '')):
            html_table += f"<tr><td>{prod.get('codigo', '-')}</td><td>{prod.get('referencia', '-')}</td><td>{prod.get('descricao', '-')}</td><td>{int(prod.get('quantidade', 0))}</td><td>R$ {prod.get('valor_unitario', 0):.2f}</td><td>R$ {prod.get('valor_total', 0):.2f}</td><td>{prod.get('fonte', '-')}</td></tr>"
        html_table += "</tbody></table>"

        return {
            "products": final_products,
            "total_products": len(final_products),
            "total_value": total_value,
            "html_table": html_table,
            "processing_info": {
                "processed_files": processed_files_count,
                "extracted_products": len(all_products)
            }
        }