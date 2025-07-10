import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    TEMP_FOLDER = os.path.join(os.getcwd(), 'temp')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # AI Models configuration
    AI_MODELS = {
        'openai': {
            'name': 'OpenAI',
            'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-4', 'gpt-3.5-turbo'],
            'default': 'gpt-4o'
        },
        'anthropic': {
            'name': 'Anthropic',
            'models': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
            'default': 'claude-3-sonnet-20240229'
        },
        'google': {
            'name': 'Google Gemini',
            'models': ['gemini-pro', 'gemini-flash', 'gemini-ultra'],
            'default': 'gemini-pro'
        },
        'deepseek': {
            'name': 'DeepSeek',
            'models': ['deepseek-chat', 'deepseek-coder', 'deepseek-67b'],
            'default': 'deepseek-chat'
        },
        'meta': {
            'name': 'Meta Llama',
            'models': ['llama-3-70b', 'llama-3-8b', 'llama-2-70b'],
            'default': 'llama-3-70b'
        },
        'mistral': {
            'name': 'Mistral AI',
            'models': ['mistral-large', 'mistral-medium', 'mistral-small'],
            'default': 'mistral-large'
        },
        'groq': {
            'name': 'Groq',
            'models': ['mixtral-8x7b-32768', 'llama2-70b-4096', 'gemma-7b-it'],
            'default': 'mixtral-8x7b-32768'
        },
        'together': {
            'name': 'Together AI',
            'models': ['meta-llama/Llama-2-70b-chat-hf', 'mistralai/Mixtral-8x7B-Instruct-v0.1'],
            'default': 'meta-llama/Llama-2-70b-chat-hf'
        },
        'fireworks': {
            'name': 'Fireworks AI',
            'models': ['accounts/fireworks/models/llama-v2-70b-chat', 'accounts/fireworks/models/mixtral-8x7b-instruct'],
            'default': 'accounts/fireworks/models/llama-v2-70b-chat'
        },
        'nvidia': {
            'name': 'NVIDIA NIM',
            'models': ['nvidia/llama3-chatqa-1.5-70b', 'nvidia/llama3-chatqa-1.5-8b'],
            'default': 'nvidia/llama3-chatqa-1.5-70b'
        }
    }
    
    # Load additional models from environment
    ADDITIONAL_MODELS = os.getenv('ADDITIONAL_MODELS', '{}')
    
    # Session settings
    SESSION_TIMEOUT = 3600  # 1 hour
