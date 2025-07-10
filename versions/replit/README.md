# Versão para Replit

Esta é a versão otimizada para execução no Replit.

## Características desta versão:
- Configurada para usar gunicorn com bind em 0.0.0.0:5000
- Sistema de gerenciamento de dependências com UV
- Variáveis de ambiente configuradas via .env
- Upload de arquivos limitado a 50 arquivos de 10MB cada

## Arquivos específicos do Replit:
- `main.py` - Ponto de entrada configurado para Replit
- `pyproject.toml` - Configuração de dependências com UV
- `.replit` - Configuração do ambiente Replit

## Como usar:
1. Clone este repositório no Replit
2. Configure as variáveis de ambiente no arquivo .env
3. Execute o comando Run para iniciar a aplicação
4. Acesse a aplicação através da URL fornecida pelo Replit