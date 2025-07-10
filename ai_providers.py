import os
import json
import logging
from typing import Dict, List, Any
import openai
from anthropic import Anthropic
import google.generativeai as genai
import requests

logger = logging.getLogger(__name__)

class AIProviderManager:
    """Manages different AI providers and their configurations"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load AI models configuration"""
        from config import Config
        config = Config.AI_MODELS.copy()
        
        # Load additional models from environment if configured
        try:
            additional = json.loads(Config.ADDITIONAL_MODELS)
            for provider, models in additional.items():
                if provider in config:
                    config[provider]['models'].extend(models.get('models', []))
                else:
                    config[provider] = models
        except (json.JSONDecodeError, AttributeError):
            pass
        
        return config
    
    def get_providers(self) -> List[Dict]:
        """Get list of available AI providers"""
        return [
            {'id': key, 'name': value['name']}
            for key, value in self.config.items()
        ]
    
    def get_models(self, provider: str) -> List[str]:
        """Get available models for a specific provider"""
        if provider not in self.config:
            raise ValueError(f"Provider '{provider}' not supported")
        
        return self.config[provider]['models']
    
    def get_client(self, provider: str, api_key: str, model: str):
        """Initialize AI client for the specified provider"""
        if provider == 'openai':
            return OpenAIClient(api_key, model)
        elif provider == 'anthropic':
            return AnthropicClient(api_key, model)
        elif provider == 'google':
            return GoogleClient(api_key, model)
        elif provider == 'deepseek':
            return DeepSeekClient(api_key, model)
        elif provider in ['meta', 'mistral', 'groq', 'together', 'fireworks', 'nvidia']:
            return GenericAPIClient(provider, api_key, model)
        else:
            raise ValueError(f"Provider '{provider}' not implemented")

class BaseAIClient:
    """Base class for AI clients"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
    
    def extract_product_data(self, text: str) -> str:
        """Extract product data from text using AI"""
        raise NotImplementedError

class OpenAIClient(BaseAIClient):
    """OpenAI client implementation"""
    
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.client = openai.OpenAI(api_key=api_key)
    
    def extract_product_data(self, text: str) -> str:
        """Extract product data using OpenAI"""
        try:
            prompt = self._get_extraction_prompt(text)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente especializado em extrair dados de produtos de documentos de pedidos de venda. Responda APENAS com JSON válido, sem texto adicional."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            if "insufficient_quota" in str(e).lower() or "quota" in str(e).lower():
                raise Exception("Entrar em contato com o Fornecedor para ativar o uso da plataforma")
            raise e
    
    def _get_extraction_prompt(self, text: str) -> str:
        """Generate extraction prompt"""
        return f"""
        Você DEVE responder APENAS com JSON válido. Não inclua texto explicativo antes ou depois do JSON.
        
        Analise o seguinte texto extraído de um pedido de venda e extraia APENAS os dados de produtos encontrados.
        
        Responda EXATAMENTE neste formato JSON:
        {{
            "produtos": [
                {{
                    "codigo": "código do produto ou null",
                    "referencia": "referência do produto ou null", 
                    "descricao": "descrição completa do produto",
                    "quantidade": número_da_quantidade,
                    "valor_unitario": valor_unitário_numérico,
                    "valor_total": valor_total_numérico
                }}
            ]
        }}
        
        REGRAS OBRIGATÓRIAS:
        - Responda APENAS com JSON válido
        - Use null para campos não disponíveis (não aspas vazias)
        - Valores numéricos devem ser números (sem símbolos de moeda)
        - Se não encontrar produtos, retorne: {{"produtos": []}}
        - NÃO inclua explicações ou texto adicional
        
        Texto para análise:
        {text}
        """

class AnthropicClient(BaseAIClient):
    """Anthropic Claude client implementation"""
    
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.client = Anthropic(api_key=api_key)
    
    def extract_product_data(self, text: str) -> str:
        """Extract product data using Anthropic Claude"""
        try:
            prompt = self._get_extraction_prompt(text)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            if "credit" in str(e).lower() or "quota" in str(e).lower():
                raise Exception("Entrar em contato com o Fornecedor para ativar o uso da plataforma")
            raise e
    
    def _get_extraction_prompt(self, text: str) -> str:
        """Generate extraction prompt for Claude"""
        return f"""
        Analise o seguinte texto extraído de um pedido de venda e extraia APENAS os dados de produtos encontrados.
        
        Para cada produto encontrado, forneça as seguintes informações no formato JSON:
        {{
            "produtos": [
                {{
                    "codigo": "código do produto (se disponível)",
                    "referencia": "referência do produto (se disponível)",
                    "descricao": "descrição completa do produto",
                    "quantidade": número_da_quantidade,
                    "valor_unitario": valor_unitário_numérico,
                    "valor_total": valor_total_numérico
                }}
            ]
        }}
        
        IMPORTANTE:
        - Se um campo não estiver disponível, use null
        - Valores numéricos devem ser apenas números (sem símbolos de moeda)
        - Extraia APENAS produtos/materiais, ignore informações de cabeçalho, rodapé, etc.
        - Se não encontrar produtos, retorne {{"produtos": []}}
        
        Texto para análise:
        {text}
        """

class GoogleClient(BaseAIClient):
    """Google Gemini client implementation"""
    
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
    
    def extract_product_data(self, text: str) -> str:
        """Extract product data using Google Gemini"""
        try:
            prompt = self._get_extraction_prompt(text)
            
            response = self.client.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 4000,
                }
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Google API error: {str(e)}")
            if "quota" in str(e).lower() or "limit" in str(e).lower():
                raise Exception("Entrar em contato com o Fornecedor para ativar o uso da plataforma")
            raise e
    
    def _get_extraction_prompt(self, text: str) -> str:
        """Generate extraction prompt for Gemini"""
        return f"""
        Analise o seguinte texto extraído de um pedido de venda e extraia APENAS os dados de produtos encontrados.
        
        Para cada produto encontrado, forneça as seguintes informações no formato JSON:
        {{
            "produtos": [
                {{
                    "codigo": "código do produto (se disponível)",
                    "referencia": "referência do produto (se disponível)",
                    "descricao": "descrição completa do produto",
                    "quantidade": número_da_quantidade,
                    "valor_unitario": valor_unitário_numérico,
                    "valor_total": valor_total_numérico
                }}
            ]
        }}
        
        IMPORTANTE:
        - Se um campo não estiver disponível, use null
        - Valores numéricos devem ser apenas números (sem símbolos de moeda)
        - Extraia APENAS produtos/materiais, ignore informações de cabeçalho, rodapé, etc.
        - Se não encontrar produtos, retorne {{"produtos": []}}
        
        Texto para análise:
        {text}
        """

class DeepSeekClient(BaseAIClient):
    """DeepSeek client implementation"""
    
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key, model)
        self.base_url = "https://api.deepseek.com/v1"
    
    def extract_product_data(self, text: str) -> str:
        """Extract product data using DeepSeek API"""
        try:
            prompt = self._get_extraction_prompt(text)
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "Você é um assistente especializado em extrair dados de produtos de documentos de pedidos de venda."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4000
                }
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                raise Exception(f"DeepSeek API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}")
            if "quota" in str(e).lower() or "credit" in str(e).lower():
                raise Exception("Entrar em contato com o Fornecedor para ativar o uso da plataforma")
            raise e
    
    def _get_extraction_prompt(self, text: str) -> str:
        """Generate extraction prompt for DeepSeek"""
        return f"""
        Analise o seguinte texto extraído de um pedido de venda e extraia APENAS os dados de produtos encontrados.
        
        Para cada produto encontrado, forneça as seguintes informações no formato JSON:
        {{
            "produtos": [
                {{
                    "codigo": "código do produto (se disponível)",
                    "referencia": "referência do produto (se disponível)",
                    "descricao": "descrição completa do produto",
                    "quantidade": número_da_quantidade,
                    "valor_unitario": valor_unitário_numérico,
                    "valor_total": valor_total_numérico
                }}
            ]
        }}
        
        IMPORTANTE:
        - Se um campo não estiver disponível, use null
        - Valores numéricos devem ser apenas números (sem símbolos de moeda)
        - Extraia APENAS produtos/materiais, ignore informações de cabeçalho, rodapé, etc.
        - Se não encontrar produtos, retorne {{"produtos": []}}
        
        Texto para análise:
        {text}
        """

class GenericAPIClient(BaseAIClient):
    """Generic API client for other providers"""
    
    def __init__(self, provider: str, api_key: str, model: str):
        super().__init__(api_key, model)
        self.provider = provider
        self.endpoints = {
            'meta': 'https://api.llama-api.com/chat/completions',
            'mistral': 'https://api.mistral.ai/v1/chat/completions',
            'groq': 'https://api.groq.com/openai/v1/chat/completions',
            'together': 'https://api.together.xyz/v1/chat/completions',
            'fireworks': 'https://api.fireworks.ai/inference/v1/chat/completions',
            'nvidia': 'https://api.nvcf.nvidia.com/v2/nvcf/pexec/functions'
        }
    
    def extract_product_data(self, text: str) -> str:
        """Extract product data using generic API"""
        try:
            prompt = self._get_extraction_prompt(text)
            endpoint = self.endpoints.get(self.provider)
            
            if not endpoint:
                raise Exception(f"Endpoint not configured for provider: {self.provider}")
            
            response = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "Você é um assistente especializado em extrair dados de produtos de documentos de pedidos de venda."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4000
                }
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                raise Exception(f"{self.provider} API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"{self.provider} API error: {str(e)}")
            if "quota" in str(e).lower() or "credit" in str(e).lower():
                raise Exception("Entrar em contato com o Fornecedor para ativar o uso da plataforma")
            raise e
    
    def _get_extraction_prompt(self, text: str) -> str:
        """Generate extraction prompt"""
        return f"""
        Analise o seguinte texto extraído de um pedido de venda e extraia APENAS os dados de produtos encontrados.
        
        Para cada produto encontrado, forneça as seguintes informações no formato JSON:
        {{
            "produtos": [
                {{
                    "codigo": "código do produto (se disponível)",
                    "referencia": "referência do produto (se disponível)",
                    "descricao": "descrição completa do produto",
                    "quantidade": número_da_quantidade,
                    "valor_unitario": valor_unitário_numérico,
                    "valor_total": valor_total_numérico
                }}
            ]
        }}
        
        IMPORTANTE:
        - Se um campo não estiver disponível, use null
        - Valores numéricos devem ser apenas números (sem símbolos de moeda)
        - Extraia APENAS produtos/materiais, ignore informações de cabeçalho, rodapé, etc.
        - Se não encontrar produtos, retorne {{"produtos": []}}
        
        Texto para análise:
        {text}
        """
