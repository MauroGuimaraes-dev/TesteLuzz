import os
import shutil
import logging
from typing import List
from flask import current_app

logger = logging.getLogger(__name__)

def allowed_file(filename: str) -> bool:
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def validate_file_size(file) -> bool:
    """Validate file size"""
    # Reset file pointer
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    return file_size <= current_app.config['MAX_CONTENT_LENGTH']

def cleanup_temp_files(session_id: str, temp_folder: str) -> None:
    """Clean up temporary files for a session"""
    try:
        # Remove session file
        session_file = os.path.join(temp_folder, f'session_{session_id}.json')
        if os.path.exists(session_file):
            os.remove(session_file)
        
        # Remove generated reports
        report_files = [
            f'pedido_compra_{session_id}.pdf',
            f'pedido_compra_{session_id}.xlsx',
            f'pedido_compra_{session_id}.csv'
        ]
        
        for report_file in report_files:
            report_path = os.path.join(temp_folder, report_file)
            if os.path.exists(report_path):
                os.remove(report_path)
        
        # Remove temporary directories that might exist
        temp_dirs = [d for d in os.listdir(temp_folder) if d.startswith('tmp') and os.path.isdir(os.path.join(temp_folder, d))]
        for temp_dir in temp_dirs:
            temp_dir_path = os.path.join(temp_folder, temp_dir)
            try:
                shutil.rmtree(temp_dir_path)
            except Exception as e:
                logger.warning(f"Could not remove temp directory {temp_dir_path}: {str(e)}")
        
        logger.info(f"Cleaned up files for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {str(e)}")

def format_currency(value: float) -> str:
    """Format currency value"""
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def format_number(value: float) -> str:
    """Format number with thousands separator"""
    return f"{value:,.0f}".replace(',', '.')

def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def validate_api_key(provider: str, api_key: str) -> bool:
    """Basic API key validation"""
    if not api_key:
        return False
    
    key_patterns = {
        'openai': api_key.startswith('sk-'),
        'anthropic': api_key.startswith('sk-ant-'),
        'google': api_key.startswith('AIzaSy'),
        'deepseek': api_key.startswith('sk-'),
        'meta': len(api_key) > 20,
        'mistral': len(api_key) > 20,
        'groq': api_key.startswith('gsk_'),
        'together': len(api_key) > 20,
        'fireworks': len(api_key) > 20,
        'nvidia': len(api_key) > 20
    }
    
    return key_patterns.get(provider, len(api_key) > 10)
