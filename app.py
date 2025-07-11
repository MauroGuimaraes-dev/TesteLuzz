import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import uuid

# Nossos módulos customizados
import database
from document_processor import DocumentProcessor
from report_generator import ReportGenerator

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURAÇÃO DA APLICAÇÃO FLASK ---
app = Flask(__name__)
# É crucial ter uma chave secreta para que as mensagens 'flash' funcionem.
app.secret_key = os.getenv('SESSION_SECRET', 'uma-chave-secreta-muito-segura-para-desenvolvimento')

# Senha do administrador (hardcoded como solicitado)
ADMIN_PASSWORD = 'Jvsg1998@0398'

# Configuração de pastas
UPLOAD_FOLDER = 'uploads'
TEMP_FOLDER = 'temp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER

# Garante que as pastas existam
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Inicializa o banco de dados ao iniciar a aplicação
# Isso garante que o arquivo 'settings.db' e a tabela sejam criados na primeira vez que o app rodar.
with app.app_context():
    database.init_db()

# --- ROTAS PRINCIPAIS DA APLICAÇÃO (PARA O USUÁRIO FINAL) ---

@app.route('/')
def index():
    """Renderiza a página inicial da aplicação para o usuário."""
    # Cria um ID de sessão único para cada visita à página.
    session_id = str(uuid.uuid4())
    return render_template('index.html', session_id=session_id)

@app.route('/process', methods=['POST'])
def process_files():
    """
    Esta rota é para o USUÁRIO. Ela recebe os arquivos, busca as configurações
    salvas pelo ADMINISTRADOR no banco de dados, e processa os documentos.
    """
    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({"error": "ID de sessão inválido."}), 400

    files = request.files.getlist('documentos')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    # 1. BUSCA AS CONFIGURAÇÕES SALVAS PELO ADMINISTRADOR NO BANCO DE DADOS.
    ai_config = database.get_ai_settings()
    if not ai_config or not ai_config.get('api_key') or 'SUA_CHAVE_API_PADRAO_AQUI' in ai_config.get('api_key'):
        return jsonify({"error": "A configuração da IA não foi definida pelo administrador."}), 500

    # Lógica para salvar os arquivos enviados em uma pasta de sessão
    session_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(session_folder, exist_ok=True)
    
    filepaths = []
    for file in files:
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(session_folder, filename)
            file.save(filepath)
            filepaths.append(filepath)

    try:
        # Instancia o processador com as configurações que vieram do banco de dados
        processor = DocumentProcessor(
            api_key=ai_config['api_key'],
            model=ai_config['model'],
            prompts=ai_config
        )
        
        # Processa os documentos
        consolidated_data = processor.process_documents(filepaths)
        
        if not consolidated_data or not consolidated_data.get('products'):
             return jsonify({"error": "A IA não conseguiu extrair dados válidos dos documentos."}), 500

        # Gera os relatórios
        report_gen = ReportGenerator()
        pdf_path = report_gen.generate_pdf(consolidated_data, session_id)
        excel_path = report_gen.generate_excel(consolidated_data, session_id)
        csv_path = report_gen.generate_csv(consolidated_data, session_id)

        # Prepara a resposta JSON para o frontend
        response_data = {
            "table_html": consolidated_data.get('html_table', '<table></table>'),
            "download_links": {
                "pdf": url_for('download_file', session_id=session_id, filename=os.path.basename(pdf_path)),
                "excel": url_for('download_file', session_id=session_id, filename=os.path.basename(excel_path)),
                "csv": url_for('download_file', session_id=session_id, filename=os.path.basename(csv_path))
            }
        }
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Erro no processamento da sessão {session_id}: {e}")
        if "authentication" in str(e).lower():
             return jsonify({"error": "Erro de autenticação. A chave API configurada pelo administrador é inválida ou não tem créditos."}), 401
        return jsonify({"error": f"Ocorreu um erro inesperado durante o processamento: {e}"}), 500


@app.route('/download/<session_id>/<filename>')
def download_file(session_id, filename):
    """Permite o download dos arquivos de relatório gerados."""
    directory = os.path.join(os.getcwd(), app.config['TEMP_FOLDER'])
    return send_from_directory(directory, filename, as_attachment=True)


# --- ROTAS DE ADMINISTRAÇÃO ---

@app.route('/login', methods=['POST'])
def login():
    """Autentica o administrador. É acionada pelo formulário de senha."""
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        # Senha correta: redireciona para a página de configurações.
        return redirect(url_for('admin_settings'))
    else:
        # Senha incorreta: volta para a página inicial com uma mensagem de erro.
        flash('Esta é uma função do Administrador do Sistema.', 'error')
        return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_settings():
    """
    Esta rota é para o ADMINISTRADOR.
    - GET: Mostra a página de configurações com os dados atuais do banco de dados.
    - POST: Recebe os dados do formulário e os salva no banco de dados.
    """
    if request.method == 'POST':
        # Coleta todos os dados do formulário de administração
        provider = request.form.get('provider')
        api_key = request.form.get('api_key')
        model = request.form.get('model')
        
        prompts = {
            "task_prompt": request.form.get('task_prompt'),
            "rules_prompt": request.form.get('rules_prompt'),
            "format_prompt": request.form.get('format_prompt'),
            "fallback_prompt": request.form.get('fallback_prompt')
        }
        
        # Chama a função do nosso módulo de banco de dados para salvar tudo
        if database.save_ai_settings(provider, api_key, model, prompts):
            flash('Configurações salvas com sucesso!', 'success')
        else:
            flash('Erro ao salvar as configurações.', 'error')
        
        # Redireciona de volta para a própria página de admin para ver a mensagem de confirmação
        return redirect(url_for('admin_settings'))

    # Se o método for GET, busca as configurações atuais e renderiza a página.
    current_settings = database.get_ai_settings()
    if not current_settings:
        # Salvaguarda: se o banco de dados estiver vazio por algum motivo, inicializa de novo.
        database.init_db()
        current_settings = database.get_ai_settings()

    return render_template('admin.html', current_settings=current_settings)

# --- PONTO DE ENTRADA DA APLICAÇÃO ---

if __name__ == '__main__':
    # O modo debug é útil para desenvolvimento local. A Render não o utiliza.
    app.run(debug=True)