import sqlite3
import logging

DATABASE_FILE = 'settings.db'
logger = logging.getLogger(__name__)

# --- PROMPTS PADRÃO ---
DEFAULT_PROMPTS = {
    "task_prompt": "Você é um assistente especializado em consolidar pedidos de materiais de arquitetura. Sua função é ler arquivos de pedidos de vendas, somar as quantidades de cada produto listado e gerar um relatório único de compra, seguindo um formato pré-definido.",
    "rules_prompt": "Siga estas regras ao processar os arquivos:\n\nAgrupe produtos iguais (mesmo nome/código) e some suas quantidades.\nIgnore produtos com quantidade zero.\nSe um produto aparecer com unidades diferentes (ex: 'un' vs. 'm²'), alerta o usuário para corrigir.\nMantenha apenas os campos relevantes: Nome do Produto, Código, Quantidade Total, Unidade.",
    "format_prompt": "O relatório final deve ser uma tabela em formato Markdown, com as seguintes colunas na ordem abaixo:\n\n| Nome do Produto | Código | Quantidade Total | Unidade |\n|---|---|---|---|\n| [Exemplo] Tinta Acrílica | TA-2030 | 15 | Litros |\n\nOrdem alfabética por nome do produto.\nNúmeros alinhados à direita, texto à esquerda.\nSe não houver código, deixe em branco.",
    "fallback_prompt": "Se um arquivo estiver corrompido ou em formato não reconhecido:\n\nPule esse arquivo e registre em um log (ex: 'Arquivo X ignorado – formato inválido').\nInforme ao usuário no final: 'X arquivos não puderam ser processados.'"
}

def get_db_connection():
    """Cria uma conexão com o banco de dados."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados e cria a tabela se não existir."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_settings (
                id INTEGER PRIMARY KEY,
                provider TEXT NOT NULL,
                api_key TEXT NOT NULL,
                model TEXT NOT NULL,
                task_prompt TEXT,
                rules_prompt TEXT,
                format_prompt TEXT,
                fallback_prompt TEXT
            )
        ''')
        # Insere uma configuração padrão se a tabela estiver vazia
        cursor.execute("SELECT COUNT(*) FROM ai_settings")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """INSERT INTO ai_settings (provider, api_key, model, task_prompt, rules_prompt, format_prompt, fallback_prompt) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ('OpenAI', 'SUA_CHAVE_API_PADRAO_AQUI', 'gpt-4o', 
                 DEFAULT_PROMPTS['task_prompt'], DEFAULT_PROMPTS['rules_prompt'], 
                 DEFAULT_PROMPTS['format_prompt'], DEFAULT_PROMPTS['fallback_prompt'])
            )
            logger.info("Banco de dados inicializado com configurações e prompts padrão.")
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao inicializar o banco de dados: {e}")

def get_ai_settings():
    """Busca todas as configurações de IA, incluindo prompts, do banco de dados."""
    try:
        conn = get_db_connection()
        settings = conn.execute('SELECT * FROM ai_settings WHERE id = 1').fetchone()
        conn.close()
        if settings:
            return dict(settings)
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar configurações: {e}")
        return None

def save_ai_settings(provider, api_key, model, prompts):
    """Salva ou atualiza as configurações de IA e os prompts no banco de dados."""
    try:
        conn = get_db_connection()
        conn.execute(
            '''UPDATE ai_settings SET 
               provider = ?, api_key = ?, model = ?, 
               task_prompt = ?, rules_prompt = ?, format_prompt = ?, fallback_prompt = ? 
               WHERE id = 1''',
            (provider, api_key, model, 
             prompts['task_prompt'], prompts['rules_prompt'], 
             prompts['format_prompt'], prompts['fallback_prompt'])
        )
        conn.commit()
        conn.close()
        logger.info("Configurações de IA e prompts salvos com sucesso.")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar configurações: {e}")
        return False