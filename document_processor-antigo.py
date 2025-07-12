import logging
from openai import OpenAI
import json
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
import io

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Processa documentos (PDF, Imagens) para extrair texto e, em seguida,
    usa um modelo de IA para extrair dados estruturados de produtos.
    """
    
    # 1. MÉTODO __INIT__ CORRIGIDO PARA ACEITAR AS CONFIGURAÇÕES
    def __init__(self, api_key: str, model: str, prompts: dict):
        """
        Inicializa o processador com as configurações da IA.
        
        :param api_key: A chave da API da OpenAI.
        :param model: O modelo de IA a ser usado (ex: 'gpt-4o').
        :param prompts: Um dicionário contendo os prompts de sistema.
        """
        if not api_key:
            raise ValueError("A chave API não pode ser vazia.")
            
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompts = prompts
        logger.info(f"DocumentProcessor inicializado com o modelo: {self.model}")

    def _extract_text_from_pdf(self, file_stream) -> str:
        """Extrai texto de um arquivo PDF."""
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
        """Extrai texto de uma imagem usando OCR (Tesseract)."""
        try:
            image = Image.open(file_stream)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto da imagem: {e}")
            return ""

    def _get_structured_data_from_ai(self, document_text: str) -> dict:
        """
        Envia o texto extraído para a IA e pede dados estruturados em JSON.
        """
        if not document_text.strip():
            return {"products": []}

        # Monta o prompt final para a IA usando as configurações do banco de dados
        system_prompt = f"""
        {self.prompts.get('task_prompt', '')}
        
        REGRAS DE PROCESSAMENTO:
        {self.prompts.get('rules_prompt', '')}
        
        FORMATO DO RELATÓRIO:
        {self.prompts.get('format_prompt', '')}
        
        REGRAS DE CONTINGÊNCIA:
        {self.prompts.get('fallback_prompt', '')}
        
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
            
            json_response = json.loads(response.choices[0].message.content)
            return json_response

        except Exception as e:
            logger.error(f"Erro na chamada da API da OpenAI: {e}")
            raise  # Re-levanta a exceção para ser tratada no app.py

    def process_documents(self, filepaths: list) -> dict:
        """
        Orquestra o processo completo: lê arquivos, extrai texto, chama a IA,
        e consolida os resultados.
        """
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
                    if structured_data and 'products' in structured_data:
                        for product in structured_data['products']:
                            product['fonte'] = os.path.basename(filepath) # Adiciona a origem
                            all_products.append(product)
                
                processed_files_count += 1
                
            except Exception as e:
                logger.error(f"Falha ao processar o arquivo {os.path.basename(filepath)}: {e}")
                continue # Pula para o próximo arquivo em caso de erro

        # Lógica de consolidação (agrupar produtos e somar quantidades)
        consolidated = {}
        for prod in all_products:
            # Cria uma chave única para cada produto (código ou descrição)
            key = prod.get('codigo') or prod.get('descricao', '').strip().lower()
            if not key:
                continue

            if key not in consolidated:
                consolidated[key] = prod.copy()
                consolidated[key]['quantidade'] = float(prod.get('quantidade', 0))
            else:
                consolidated[key]['quantidade'] += float(prod.get('quantidade', 0))

        final_products = list(consolidated.values())
        
        # Recalcula o valor total após a consolidação
        total_value = 0
        for prod in final_products:
            prod['valor_total'] = prod['quantidade'] * float(prod.get('valor_unitario', 0))
            total_value += prod['valor_total']

        return {
            "products": final_products,
            "total_products": len(final_products),
            "total_value": total_value,
            "processing_info": {
                "processed_files": processed_files_count,
                "extracted_products": len(all_products)
            }
        }