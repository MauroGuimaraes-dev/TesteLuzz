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

        system_prompt = f"""
        {self.prompts.get('task_prompt', '')}
        REGRAS DE PROCESSAMENTO: {self.prompts.get('rules_prompt', '')}
        FORMATO DO RELATÓRIO: {self.prompts.get('format_prompt', '')}
        REGRAS DE CONTINGÊNCIA: {self.prompts.get('fallback_prompt', '')}
        Responda APENAS com um objeto JSON válido.
        """
        user_prompt = f"Por favor, analise o seguinte texto e extraia os dados dos produtos no formato JSON solicitado:\n\n---INÍCIO DO TEXTO---\n{document_text}\n---FIM DO TEXTO---"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            response_content = response.choices[0].message.content
            
            # --- MUDANÇA CRÍTICA PARA ROBUSTEZ ---
            # Tenta carregar o JSON. Se falhar, ou se não for um dicionário,
            # retorna um dicionário vazio, evitando que o programa quebre.
            try:
                json_response = json.loads(response_content)
                if not isinstance(json_response, dict):
                    logger.warning("Resposta da IA não é um dicionário. Retornando vazio.")
                    return {} # Retorna um dicionário vazio se não for um dict
            except json.JSONDecodeError:
                logger.error(f"Falha ao decodificar JSON da IA. Resposta recebida: {response_content}")
                return {} # Retorna um dicionário vazio em caso de erro de JSON

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
                    
                    # --- MUDANÇA CRÍTICA PARA ROBUSTEZ ---
                    # Verifica se a chave 'products' existe e se é uma lista antes de iterar
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

        # Se depois de todos os arquivos, nenhum produto foi extraído, retorna None
        if not all_products:
            return None

        # Lógica de consolidação
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