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
app.secret_key = os.getenv('SESSION_SECRET', 'uma-chave-secreta-muito-segura-para-desenvolvimento')

ADMIN_PASSWORD = 'Jvsg1998@0398'

UPLOAD_FOLDER = 'uploads'
TEMP_FOLDER = 'temp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

with app.app_context():
    database.init_db()

# --- ROTAS PRINCIPAIS DA APLICAÇÃO ---

@app.route('/')
def index():
    session_id = str(uuid.uuid4())
    return render_template('index.html', session_id=session_id)

@app.route('/process', methods=['POST'])
def process_files():
    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({"error": "ID de sessão inválido."}), 400

    files = request.files.getlist('documentos')
    if not files or all(f.filename == '' for f in files):
        return jsonify({"error": "Nenhum arquivo selecionado."}), 400

    ai_config = database.get_ai_settings()
    if not ai_config or not ai_config.get('api_key') or 'SUA_CHAVE_API_PADRAO_AQUI' in ai_config.get('api_key'):
        return jsonify({"error": "A configuração da IA não foi definida pelo administrador."}), 500

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
        processor = DocumentProcessor(
            api_key=ai_config['api_key'],
            model=ai_config['model'],
            prompts=ai_config
        )
        
        consolidated_data = processor.process_documents(filepaths)
        
        if not consolidated_data or not consolidated_data.get('products'):
             return jsonify({"error": "A IA não conseguiu extrair dados válidos dos documentos."}), 500

        report_gen = ReportGenerator()
        pdf_path = report_gen.generate_pdf(consolidated_data, session_id)
        excel_path = report_gen.generate_excel(consolidated_data, session_id)
        csv_path = report_gen.generate_csv(consolidated_data, session_id)

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
    directory = os.path.join(os.getcwd(), app.config['TEMP_FOLDER'])
    return send_from_directory(directory, filename, as_attachment=True)

# --- NOVA ROTA PARA RESOLVER O ERRO 404 ---
@app.route('/api/models/<provider>')
def get_models(provider):
    """Retorna uma lista de modelos para um provedor de IA específico."""
    if provider.lower() == 'openai':
        # No futuro, isso poderia vir de um banco de dados ou de uma chamada de API.
        # Por agora, uma lista fixa é perfeita.
        models = [
            {"id": "gpt-4o", "name": "GPT-4o (Mais Recente)"},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo (Mais Rápido)"}
        ]
        return jsonify(models)
    
    # Retorna uma lista vazia para provedores não conhecidos
    return jsonify([])


# --- ROTAS DE ADMINISTRAÇÃO ---

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password')
    if password == ADMIN_PASSWORD:
        return redirect(url_for('admin_settings'))
    else:
        flash('Esta é uma função do Administrador do Sistema.', 'error')
        return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_settings():
    if request.method == 'POST':
        provider = request.form.get('provider')
        api_key = request.form.get('api_key')
        model = request.form.get('model')
        
        prompts = {
            "task_prompt": request.form.get('task_prompt'),
            "rules_prompt": request.form.get('rules_prompt'),
            "format_prompt": request.form.get('format_prompt'),
            "fallback_prompt": request.form.get('fallback_prompt')
        }
        
        if database.save_ai_settings(provider, api_key, model, prompts):
            flash('Configurações salvas com sucesso!', 'success')
        else:
            flash('Erro ao salvar as configurações.', 'error')
        
        return redirect(url_for('admin_settings'))

    current_settings = database.get_ai_settings()
    if not current_settings:
        database.init_db()
        current_settings = database.get_ai_settings()

    return render_template('admin.html', current_settings=current_settings)

# --- PONTO DE ENTRADA DA APLICAÇÃO ---

if __name__ == '__main__':
    app.run(debug=True)