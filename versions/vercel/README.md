# Versão para Vercel

Esta é a versão otimizada para deployment no Vercel.

## Características desta versão:
- Configurada para usar serverless functions
- Sistema de upload de arquivos otimizado para Vercel
- Variáveis de ambiente configuradas via Vercel Dashboard
- Configuração específica para Python runtime no Vercel

## Arquivos específicos do Vercel:
- `vercel.json` - Configuração de deployment
- `api/` - Pasta com as funções serverless
- `requirements.txt` - Dependências Python para Vercel
- `static/` - Arquivos estáticos servidos pelo Vercel

## Limitações no Vercel:
- Tempo limite de execução de 10 segundos (pode ser aumentado no plano pago)
- Limite de tamanho de arquivo de 4.5MB (pode ser contornado com upload direto)
- Processamento de arquivos grandes pode precisar de otimizações

## Como fazer deploy:
1. Conecte seu repositório GitHub ao Vercel
2. Configure as variáveis de ambiente no dashboard do Vercel
3. O deploy será automático a cada push para a branch main
4. Acesse através da URL fornecida pelo Vercel