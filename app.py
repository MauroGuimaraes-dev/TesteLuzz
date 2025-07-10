import os
import logging
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix
import tempfile
import shutil
from datetime import datetime
import json

from config import Config
from ai_providers import AIProviderManager
from document_processor import DocumentProcessor
from report_generator import ReportGenerator
from utils import allowed_file, validate_file_size, cleanup_temp_files

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize managers
ai_manager = AIProviderManager()
doc_processor = DocumentProcessor()
report_generator = ReportGenerator()

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Main page with upload interface"""
    providers = ai_manager.get_providers()
    return render_template('index.html', providers=providers)

@app.route('/api/models/<provider>')
def get_models(provider):
    """Get available models for a specific provider"""
    try:
        models = ai_manager.get_models(provider)
        return jsonify({'success': True, 'models': models})
    except Exception as e:
        logger.error(f"Error getting models for {provider}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file upload and processing"""
    try:
        # Get form data
        provider = request.form.get('provider', 'openai')
        api_key = request.form.get('api_key', '')
        model = request.form.get('model', 'gpt-4o')
        
        # Validate API key format first to avoid wasting credits
        if not api_key:
            return jsonify({'success': False, 'error': 'Chave API é obrigatória'}), 400
        
        # Basic format validation to prevent obvious errors
        from utils import validate_api_key
        if not validate_api_key(provider, api_key):
            return jsonify({
                'success': False, 
                'error': f'Formato de chave API inválido para {provider}. Verifique se a chave está correta.',
                'show_modal': True
            }), 400
        
        # Get uploaded files
        files = request.files.getlist('files')
        if not files or len(files) == 0:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        
        if len(files) > 50:
            return jsonify({'success': False, 'error': 'Máximo de 50 arquivos permitidos'}), 400
        
        # Create temporary directory for this processing session
        temp_dir = tempfile.mkdtemp(dir=app.config['TEMP_FOLDER'])
        uploaded_files = []
        
        try:
            # Validate and save files
            for file in files:
                if file.filename == '':
                    continue
                
                if not allowed_file(file.filename):
                    return jsonify({'success': False, 'error': f'Formato de arquivo não suportado: {file.filename}'}), 400
                
                if not validate_file_size(file):
                    return jsonify({'success': False, 'error': f'Arquivo muito grande: {file.filename}. Máximo 10MB'}), 400
                
                filename = secure_filename(file.filename)
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                uploaded_files.append(filepath)
            
            if not uploaded_files:
                return jsonify({'success': False, 'error': 'Nenhum arquivo válido encontrado'}), 400
            
            # Initialize AI provider
            try:
                ai_client = ai_manager.get_client(provider, api_key, model)
            except Exception as e:
                logger.error(f"Error initializing AI client: {str(e)}")
                return jsonify({
                    'success': False, 
                    'error': 'Erro ao conectar com o provedor de IA. Verifique sua chave API e tente novamente.',
                    'show_modal': True
                }), 400
            
            # Process documents
            session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            results = doc_processor.process_files(uploaded_files, ai_client, session_id)
            
            # Check if processing was successful
            if not results or 'products' not in results:
                return jsonify({'success': False, 'error': 'Erro no processamento dos documentos'}), 500
            
            # Store results in session (in production, use Redis or similar)
            session_data = {
                'session_id': session_id,
                'results': results,
                'temp_dir': temp_dir,
                'provider': provider,
                'model': model
            }
            
            # For now, store in a simple file (in production, use proper session storage)
            session_file = os.path.join(app.config['TEMP_FOLDER'], f'session_{session_id}.json')
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'results': results
            })
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e
            
    except Exception as e:
        logger.error(f"Error in upload_files: {str(e)}")
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/generate_report/<session_id>/<format>')
def generate_report(session_id, format):
    """Generate and download report in specified format"""
    try:
        # Load session data
        session_file = os.path.join(app.config['TEMP_FOLDER'], f'session_{session_id}.json')
        if not os.path.exists(session_file):
            return jsonify({'success': False, 'error': 'Sessão não encontrada'}), 404
        
        with open(session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        results = session_data['results']
        
        # Generate report
        if format == 'pdf':
            file_path = report_generator.generate_pdf(results, session_id)
            mimetype = 'application/pdf'
        elif format == 'excel':
            file_path = report_generator.generate_excel(results, session_id)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif format == 'csv':
            file_path = report_generator.generate_csv(results, session_id)
            mimetype = 'text/csv'
        else:
            return jsonify({'success': False, 'error': 'Formato não suportado'}), 400
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f'pedido_compra_{session_id}.{format}',
            mimetype=mimetype
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'success': False, 'error': f'Erro ao gerar relatório: {str(e)}'}), 500

@app.route('/api/cleanup/<session_id>', methods=['POST'])
def cleanup_session(session_id):
    """Clean up session files"""
    try:
        cleanup_temp_files(session_id, app.config['TEMP_FOLDER'])
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error cleaning up session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': 'Arquivo muito grande. Máximo 10MB por arquivo.'}), 413

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
