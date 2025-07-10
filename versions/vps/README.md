# Versão para VPS (Hostinger/Contabo)

Esta é a versão otimizada para deployment em VPS tradicionais.

## Características desta versão:
- Configurada para usar nginx + gunicorn
- Sistema de upload de arquivos com maior capacidade
- Configuração para SSL/TLS com Let's Encrypt
- Sistema de logs e monitoramento
- Backup automático de dados

## Arquivos específicos para VPS:
- `nginx.conf` - Configuração do nginx
- `gunicorn.conf.py` - Configuração do gunicorn
- `systemd/` - Arquivos de service para systemd
- `docker-compose.yml` - Configuração Docker (opcional)
- `install.sh` - Script de instalação automatizada

## Recursos adicionais para VPS:
- Processamento de até 100 arquivos simultâneos
- Arquivos de até 50MB cada
- Sistema de cache Redis (opcional)
- Banco de dados PostgreSQL
- Sistema de backup automático

## Instalação no VPS:

### Pré-requisitos:
- Ubuntu 20.04+ ou CentOS 8+
- Python 3.11+
- Nginx
- PostgreSQL (opcional)
- Redis (opcional)

### Instalação manual:
```bash
# 1. Clone o repositório
git clone <repository_url>
cd consolidador-pedidos

# 2. Execute o script de instalação
sudo chmod +x install.sh
sudo ./install.sh

# 3. Configure as variáveis de ambiente
sudo nano /etc/environment

# 4. Reinicie os serviços
sudo systemctl restart nginx
sudo systemctl restart consolidador-pedidos
```

### Instalação com Docker:
```bash
# 1. Clone o repositório
git clone <repository_url>
cd consolidador-pedidos

# 2. Configure as variáveis no docker-compose.yml
nano docker-compose.yml

# 3. Execute com docker-compose
docker-compose up -d
```

## Configuração de domínio:
1. Aponte seu domínio para o IP do VPS
2. Configure SSL com Let's Encrypt:
```bash
sudo certbot --nginx -d seudominio.com
```

## Monitoramento:
- Logs disponíveis em `/var/log/consolidador-pedidos/`
- Métricas via sistema de monitoramento integrado
- Alertas por email configuráveis