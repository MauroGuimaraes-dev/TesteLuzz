import os
import json
import logging
from typing import List, Dict, Any
from PIL import Image
import pytesseract
import PyPDF2
import io
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes uploaded documents and extracts product data"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg']
    
    def process_files(self, file_paths: List[str], ai_client, session_id: str) -> Dict[str, Any]:
        """Process multiple files and extract product data"""
        try:
            all_products = []
            processing_info = {
                'total_files': len(file_paths),
                'processed_files': 0,
                'failed_files': [],
                'extracted_products': 0
            }
            
            for file_path in file_paths:
                try:
                    logger.info(f"Processing file: {file_path}")
                    
                    # Extract text from file
                    text = self._extract_text_from_file(file_path)
                    
                    if not text.strip():
                        logger.warning(f"No text extracted from {file_path}")
                        processing_info['failed_files'].append({
                            'file': os.path.basename(file_path),
                            'error': 'Texto não encontrado no arquivo'
                        })
                        continue
                    
                    # Use AI to extract product data
                    ai_response = ai_client.extract_product_data(text)
                    
                    # Parse AI response
                    products = self._parse_ai_response(ai_response, file_path)
                    
                    if products:
                        all_products.extend(products)
                        processing_info['extracted_products'] += len(products)
                        logger.info(f"Extracted {len(products)} products from {file_path}")
                    
                    processing_info['processed_files'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
                    processing_info['failed_files'].append({
                        'file': os.path.basename(file_path),
                        'error': str(e)
                    })
            
            # Consolidate duplicate products
            consolidated_products = self._consolidate_products(all_products)
            
            # Calculate totals
            total_value = sum(p['valor_total'] for p in consolidated_products)
            
            return {
                'session_id': session_id,
                'processing_info': processing_info,
                'products': consolidated_products,
                'total_products': len(consolidated_products),
                'total_value': total_value,
                'timestamp': session_id
            }
            
        except Exception as e:
            logger.error(f"Error in process_files: {str(e)}")
            raise e
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """Extract text from file based on its format"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self._extract_text_from_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg']:
            return self._extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            # If PDF text extraction fails, try OCR
            return self._extract_text_from_image(file_path)
    
    def _extract_text_from_image(self, file_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            # Open and preprocess image
            image = Image.open(file_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Improve image quality for OCR
            image = self._preprocess_image(image)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image, lang='por')
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {str(e)}")
            raise e
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        try:
            # Resize image if too small
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000 / width, 1000 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.LANCZOS)
            
            return image
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            return image
    
    def _parse_ai_response(self, ai_response: str, source_file: str) -> List[Dict[str, Any]]:
        """Parse AI response to extract product data"""
        try:
            # Clean the response to extract JSON
            cleaned_response = self._clean_json_response(ai_response)
            
            # Parse JSON
            data = json.loads(cleaned_response)
            
            products = []
            if 'produtos' in data and isinstance(data['produtos'], list):
                for product_data in data['produtos']:
                    product = self._normalize_product_data(product_data, source_file)
                    if product:
                        products.append(product)
            
            return products
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Response: {ai_response}")
            return []
        except Exception as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return []
    
    def _clean_json_response(self, response: str) -> str:
        """Clean AI response to extract valid JSON"""
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Find JSON object
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return response
    
    def _normalize_product_data(self, product_data: Dict, source_file: str) -> Dict[str, Any]:
        """Normalize product data from AI response"""
        try:
            # Extract and clean data
            codigo = product_data.get('codigo') or ''
            referencia = product_data.get('referencia') or ''
            descricao = product_data.get('descricao') or ''
            
            # Skip if no description
            if not descricao.strip():
                return None
            
            # Parse numeric values
            quantidade = self._parse_numeric_value(product_data.get('quantidade', 0))
            valor_unitario = self._parse_numeric_value(product_data.get('valor_unitario', 0))
            valor_total = self._parse_numeric_value(product_data.get('valor_total', 0))
            
            # Calculate missing values
            if valor_total == 0 and quantidade > 0 and valor_unitario > 0:
                valor_total = quantidade * valor_unitario
            elif valor_unitario == 0 and quantidade > 0 and valor_total > 0:
                valor_unitario = valor_total / quantidade
            
            return {
                'codigo': codigo.strip(),
                'referencia': referencia.strip(),
                'descricao': descricao.strip(),
                'quantidade': quantidade,
                'valor_unitario': valor_unitario,
                'valor_total': valor_total,
                'fonte': os.path.basename(source_file)
            }
            
        except Exception as e:
            logger.error(f"Error normalizing product data: {str(e)}")
            return None
    
    def _parse_numeric_value(self, value) -> float:
        """Parse numeric value from various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove currency symbols and spaces
            cleaned = re.sub(r'[R$\s,.]', '', value)
            cleaned = re.sub(r'[^\d]', '', cleaned)
            
            try:
                return float(cleaned) / 100 if cleaned else 0.0
            except ValueError:
                return 0.0
        
        return 0.0
    
    def _consolidate_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidate duplicate products"""
        consolidated = {}
        
        for product in products:
            # Create a unique key for product identification
            key = self._generate_product_key(product)
            
            if key in consolidated:
                # Merge duplicate products
                existing = consolidated[key]
                existing['quantidade'] += product['quantidade']
                existing['valor_total'] += product['valor_total']
                
                # Update average unit price
                if existing['quantidade'] > 0:
                    existing['valor_unitario'] = existing['valor_total'] / existing['quantidade']
                
                # Combine sources
                if product['fonte'] not in existing['fonte']:
                    existing['fonte'] += f", {product['fonte']}"
            else:
                consolidated[key] = product.copy()
        
        # Sort by description
        return sorted(consolidated.values(), key=lambda x: x['descricao'])
    
    def _generate_product_key(self, product: Dict[str, Any]) -> str:
        """Generate unique key for product identification"""
        # Priority: codigo > referencia > description similarity
        if product['codigo']:
            return f"codigo_{product['codigo']}"
        elif product['referencia']:
            return f"ref_{product['referencia']}"
        else:
            # Use normalized description
            desc = product['descricao'].lower().strip()
            desc = re.sub(r'[^\w\s]', '', desc)
            desc = re.sub(r'\s+', ' ', desc)
            return f"desc_{desc}"
