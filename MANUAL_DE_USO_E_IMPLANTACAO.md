# Manual de Uso e Implantação
## Consolidador de Pedidos de Compra com IA

### Índice
1. [Visão Geral](#visão-geral)
2. [Versão Replit](#versão-replit)
3. [Versão Vercel](#versão-vercel)  
4. [Versão VPS](#versão-vps)
5. [Configuração de Chaves API](#configuração-de-chaves-api)
6. [Solução de Problemas](#solução-de-problemas)

---

## Visão Geral

O Consolidador de Pedidos de Compra é uma aplicação web que utiliza Inteligência Artificial para processar múltiplos documentos (PDF, PNG, JPG, JPEG) e gerar pedidos de compra consolidados.

### Características Principais:
- **Processamento**: Até 50 arquivos simultâneos de 10MB cada
- **Formatos**: PDF, PNG, JPG, JPEG
- **IA**: 10 provedores diferentes (OpenAI, Anthropic, Google Gemini, etc.)
- **Exportação**: PDF, Excel (XLSX), CSV
- **OCR**: Reconhecimento de texto em imagens
- **Consolidação**: Identificação automática de produtos duplicados

---

## Versão Replit

### Características
- Execução direta no ambiente Replit
- Configuração automática de dependências
- Interface web acessível via URL do Replit

### Instalação no Replit

1. **Acesse este projeto no Replit**
   - URL: [Link do seu projeto]
   - Ou importe via GitHub

2. **Configure as variáveis de ambiente**
   ```bash
   # Clique em "Secrets" no painel lateral
   # Adicione:
   SESSION_SECRET=sua-chave-secreta-aqui
   ```

3. **Execute a aplicação**
   ```bash
   # Clique no botão "Run" ou execute:
   python main.py
   ```

4. **Acesse a aplicação**
   - URL será mostrada no painel do Replit
   - Formato: `https://seu-projeto.replit.app`

### Configuração Adicional
- **Modelos personalizados**: Edite o arquivo `.env` para adicionar novos modelos:
  ```bash
  ADDITIONAL_MODELS={"openai": {"models": ["gpt-4-turbo", "gpt-4-vision"]}}
  ```

### Limitações no Replit
- Tempo de execução limitado para contas gratuitas
- Processamento de arquivos grandes pode ser mais lento
- Armazenamento temporário apenas

---

## Versão Vercel

### Características
- Deployment serverless automático
- Escalabilidade automática
- CDN global integrado
- SSL automático

### Instalação no Vercel

1. **Prepare o repositório**
   ```bash
   # Clone o projeto
   git clone [url-do-repositorio]
   cd consolidador-pedidos
   
   # Copie os arquivos da versão Vercel
   cp -r versions/vercel/* .
   ```

2. **Configure o projeto no Vercel**
   ```bash
   # Instale a CLI do Vercel
   npm i -g vercel
   
   # Faça login
   vercel login
   
   # Configure o projeto
   vercel
   ```

3. **Configure as variáveis de ambiente**
   ```bash
   # No dashboard do Vercel ou via CLI:
   vercel env add SESSION_SECRET
   # Insira sua chave secreta
   ```

4. **Deploy automático**
   ```bash
   # Push para GitHub ativa deploy automático
   git add .
   git commit -m "Deploy to Vercel"
   git push origin main
   ```

### Configuração Específica Vercel

**Arquivo `vercel.json`:**
```json
{
  "version": 2,
  "builds": [
    {"src": "api/index.py", "use": "@vercel/python"}
  ],
  "routes": [
    {"src": "/(.*)", "dest": "/api/index.py"}
  ],
  "functions": {
    "api/index.py": {"maxDuration": 30}
  }
}
```

### Limitações no Vercel
- **Tempo de execução**: 10s (gratuito) / 30s (pago)
- **Tamanho de arquivo**: 4.5MB máximo
- **Memória**: 1024MB máximo
- **Processamento**: Pode precisar otimizar para arquivos grandes

### Soluções para Limitações
1. **Arquivos grandes**: Implementar upload direto para cloud storage
2. **Timeout**: Dividir processamento em múltiplas funções
3. **Memória**: Processar arquivos sequencialmente

---

## Versão VPS

### Características
- Máximo controle e performance
- Processamento até 100 arquivos simultâneos
- Arquivos até 50MB cada
- Banco de dados PostgreSQL
- Cache Redis
- Backup automático

### Pré-requisitos

**Sistema Operacional:**
- Ubuntu 20.04+ ou CentOS 8+
- Mínimo 2GB RAM, 20GB disco
- Python 3.11+

**Dependências do Sistema:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-dev python3.11-venv
sudo apt install -y nginx postgresql redis-server
sudo apt install -y tesseract-ocr tesseract-ocr-por
sudo apt install -y git curl certbot python3-certbot-nginx
```

### Instalação Automática

1. **Download e execução do script**
   ```bash
   # Clone o repositório
   git clone [url-do-repositorio]
   cd consolidador-pedidos
   
   # Copie os arquivos VPS
   cp -r versions/vps/* .
   
   # Execute a instalação automática
   chmod +x install.sh
   sudo ./install.sh
   ```

2. **O script automaticamente:**
   - Instala todas as dependências
   - Configura nginx e PostgreSQL
   - Cria usuário do sistema
   - Configura services do systemd
   - Estabelece firewall e segurança
   - Configura backup automático

### Instalação Manual

1. **Preparação do ambiente**
   ```bash
   # Criar usuário da aplicação
   sudo useradd --system --shell /bin/bash --home /opt/consolidador --create-home consolidador
   
   # Copiar arquivos
   sudo cp -r . /opt/consolidador/app/
   sudo chown -R consolidador:consolidador /opt/consolidador
   ```

2. **Configuração Python**
   ```bash
   # Mudar para usuário da aplicação
   sudo -u consolidador bash
   cd /opt/consolidador/app
   
   # Criar ambiente virtual
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configuração do banco**
   ```bash
   # PostgreSQL
   sudo -u postgres createdb consolidador
   sudo -u postgres createuser consolidador
   sudo -u postgres psql -c "ALTER USER consolidador PASSWORD 'senha_segura';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE consolidador TO consolidador;"
   ```

4. **Configuração Nginx**
   ```bash
   # Copiar configuração
   sudo cp nginx.conf /etc/nginx/sites-available/consolidador
   sudo ln -s /etc/nginx/sites-available/consolidador /etc/nginx/sites-enabled/
   sudo rm /etc/nginx/sites-enabled/default
   
   # Testar configuração
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Service systemd**
   ```bash
   # Copiar service
   sudo cp consolidador.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable consolidador
   sudo systemctl start consolidador
   ```

### Instalação com Docker

1. **Usando Docker Compose**
   ```bash
   # Copiar arquivos
   cp -r versions/vps/* .
   
   # Configurar variáveis
   cp .env.example .env
   nano .env
   
   # Executar
   docker-compose up -d
   ```

2. **Configuração SSL**
   ```bash
   # Após configurar domínio
   sudo certbot --nginx -d seudominio.com
   ```

### Configuração de Domínio

1. **DNS**
   ```bash
   # Aponte seu domínio para o IP do servidor
   A     @     IP.DO.SERVIDOR
   CNAME www   seudominio.com
   ```

2. **SSL com Let's Encrypt**
   ```bash
   # Certificado automático
   sudo certbot --nginx -d seudominio.com -d www.seudominio.com
   
   # Renovação automática
   sudo crontab -e
   # Adicionar: 0 12 * * * /usr/bin/certbot renew --quiet
   ```

### Monitoramento e Manutenção

**Comandos de gerenciamento:**
```bash
# Status dos serviços
sudo systemctl status consolidador
sudo systemctl status nginx
sudo systemctl status postgresql

# Logs
sudo journalctl -u consolidador -f
sudo tail -f /opt/consolidador/app/logs/access.log

# Restart dos serviços
sudo systemctl restart consolidador
sudo systemctl restart nginx

# Backup manual
sudo -u consolidador /opt/consolidador/backup.sh
```

**Monitoramento de recursos:**
```bash
# Uso de CPU/Memória
htop

# Espaço em disco
df -h

# Logs do sistema
tail -f /var/log/syslog
```

---

## Configuração de Chaves API

### OpenAI
1. **Acesse**: https://platform.openai.com/api-keys
2. **Crie nova chave**: "Create new secret key"
3. **Formato**: `sk-proj-...` ou `sk-...`
4. **Modelos disponíveis**: gpt-4o, gpt-4o-mini, gpt-4, gpt-3.5-turbo

### Anthropic
1. **Acesse**: https://console.anthropic.com/
2. **Vá para**: Account Settings > API Keys
3. **Formato**: `sk-ant-...`
4. **Modelos**: claude-3-opus, claude-3-sonnet, claude-3-haiku

### Google Gemini
1. **Acesse**: https://aistudio.google.com/app/apikey
2. **Crie nova chave**: "Create API key"
3. **Formato**: `AIzaSy...`
4. **Modelos**: gemini-pro, gemini-flash

### DeepSeek
1. **Acesse**: https://platform.deepseek.com/api_keys
2. **Crie nova chave**: "Create new key"
3. **Formato**: `sk-...`
4. **Modelos**: deepseek-chat, deepseek-coder

### Outros Provedores
- **Groq**: https://console.groq.com/keys (formato: `gsk_...`)
- **Mistral**: https://console.mistral.ai/ 
- **Together AI**: https://api.together.xyz/settings/api-keys
- **Fireworks**: https://fireworks.ai/account/api-keys
- **NVIDIA NIM**: https://build.nvidia.com/

---

## Solução de Problemas

### Problemas Comuns

#### 1. Erro "Entrar em contato com o Fornecedor"
**Causa**: Sem créditos na conta da IA
**Solução**: 
- Verifique saldo na conta do provedor
- Configure método de pagamento
- Teste com outro provedor

#### 2. Erro de JSON parsing
**Causa**: IA retornou HTML ou texto inválido
**Solução**: 
- Sistema já trata automaticamente
- Verifica chave API
- Tenta novamente

#### 3. OCR não funciona
**Causa**: Tesseract não instalado
**Solução**:
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-por

# CentOS/RHEL
sudo yum install tesseract tesseract-langpack-por
```

#### 4. Upload de arquivo falha
**Causa**: Arquivo muito grande ou formato inválido
**Solução**:
- Reduzir tamanho para menos de 10MB
- Verificar formato (PDF, PNG, JPG, JPEG)
- Tentar com menos arquivos

#### 5. Timeout no processamento
**Causa**: Muitos arquivos ou arquivos grandes
**Solução**:
- Processar menos arquivos por vez
- Verificar conexão de internet
- Aumentar timeout (VPS)

### Logs e Debugging

#### Replit
```bash
# Ver logs no console do Replit
# Usar debugger integrado
```

#### Vercel
```bash
# Dashboard do Vercel > Functions > View Function Logs
# Runtime logs em tempo real
```

#### VPS
```bash
# Logs da aplicação
sudo journalctl -u consolidador -f

# Logs do nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs da aplicação
tail -f /opt/consolidador/app/logs/access.log
tail -f /opt/consolidador/app/logs/error.log
```

### Performance e Otimização

#### Replit
- Usar plano pago para melhor performance
- Otimizar número de arquivos processados

#### Vercel
- Configurar timeout máximo
- Implementar cache de resultados
- Usar edge functions quando possível

#### VPS
- Aumentar workers do gunicorn
- Configurar cache Redis
- Otimizar configuração PostgreSQL
- Usar SSD para storage

### Backup e Recuperação

#### Dados importantes:
- Configurações: `.env`, `config.py`
- Uploads: pasta `uploads/`
- Logs: pasta `logs/`
- Banco (VPS): PostgreSQL dump

#### Backup automático (VPS):
```bash
# Executado diariamente pelo cron
/opt/consolidador/backup.sh

# Restaurar backup
pg_dump -h localhost -U consolidador -d consolidador < backup.sql
```

### Suporte e Atualizações

#### Como obter suporte:
1. Verificar logs de erro
2. Consultar este manual
3. Verificar issues no GitHub
4. Contatar desenvolvedor

#### Atualizações:
```bash
# Replit: Pull from GitHub
# Vercel: Push para branch main
# VPS: Pull + restart services
cd /opt/consolidador/app
git pull origin main
sudo systemctl restart consolidador
```

---

## Checklist de Implantação

### Replit ✅
- [ ] Projeto importado/criado
- [ ] Variáveis de ambiente configuradas
- [ ] Aplicação executando
- [ ] Teste com arquivo de exemplo
- [ ] Chaves API configuradas

### Vercel ✅
- [ ] Repositório GitHub conectado
- [ ] Projeto configurado no Vercel
- [ ] Variáveis de ambiente definidas
- [ ] Deploy executado com sucesso
- [ ] Domínio personalizado (opcional)
- [ ] Teste de funcionalidade

### VPS ✅
- [ ] Servidor provisionado
- [ ] Dependências instaladas
- [ ] Aplicação configurada
- [ ] Nginx configurado
- [ ] SSL configurado
- [ ] Firewall configurado
- [ ] Backup automático configurado
- [ ] Monitoramento ativo
- [ ] Teste completo realizado

---

*Desenvolvido para processamento eficiente de pedidos de compra usando IA*