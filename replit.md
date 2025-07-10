# Purchase Order Consolidator with AI

## Overview

This Flask-based web application consolidates purchase orders from multiple document formats (PDF, PNG, JPG, JPEG) using various AI providers. The system can process up to 50 files simultaneously (up to 10MB each) and generate consolidated purchase order reports in PDF, Excel, and CSV formats.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: HTML/CSS/JavaScript with Bootstrap for responsive design
- **Theme**: Dark theme with Bootstrap integration
- **Components**: 
  - Provider selection dropdown
  - API key input with visibility toggle
  - File upload interface with drag-and-drop
  - Progress tracking and report generation
- **Assets**: Custom CSS and JavaScript for enhanced UX

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Structure**: Modular design with separate managers for different concerns
- **Components**:
  - `app.py`: Main Flask application with routes
  - `ai_providers.py`: AI provider management and client creation
  - `document_processor.py`: Document text extraction and processing
  - `report_generator.py`: Multi-format report generation
  - `config.py`: Configuration management
  - `utils.py`: Utility functions for file handling

### Key Design Patterns
- **Manager Pattern**: Separate managers for AI providers, document processing, and report generation
- **Configuration Management**: Centralized configuration with environment variable support
- **Error Handling**: Comprehensive logging and error management throughout

## Key Components

### AI Provider Management
- **Supported Providers**: OpenAI, Anthropic, Google Gemini, DeepSeek, Meta Llama, Mistral AI, Groq, Together AI, Fireworks AI, NVIDIA NIM
- **Dynamic Model Loading**: Models are loaded based on provider selection
- **API Key Management**: Secure handling of API keys with format validation
- **Extensibility**: Support for additional models via environment configuration

### Document Processing
- **Supported Formats**: PDF, PNG, JPG, JPEG files
- **Text Extraction**: OCR for images, text extraction for PDFs
- **Batch Processing**: Handles up to 50 files simultaneously
- **Error Handling**: Individual file processing with failure tracking

### Report Generation
- **Multiple Formats**: PDF, Excel (XLSX), CSV output
- **Professional Styling**: Formatted reports with tables and summaries
- **Temporary File Management**: Secure temporary file handling with cleanup

## Data Flow

1. **User Input**: Provider selection, API key entry, file upload
2. **File Processing**: Text extraction from uploaded documents
3. **AI Processing**: Product data extraction using selected AI provider
4. **Data Consolidation**: Aggregation of products from all processed files
5. **Report Generation**: Creation of consolidated purchase order reports
6. **File Delivery**: Secure download of generated reports
7. **Cleanup**: Automatic removal of temporary files

## External Dependencies

### AI Providers
- **OpenAI**: GPT models for text analysis
- **Anthropic**: Claude models for document processing
- **Google**: Gemini models for data extraction
- **Other Providers**: DeepSeek, Meta Llama, Mistral, Groq, Together AI, Fireworks, NVIDIA NIM

### Document Processing Libraries
- **PyPDF2**: PDF text extraction
- **Pillow (PIL)**: Image processing
- **pytesseract**: OCR for image-to-text conversion

### Report Generation Libraries
- **ReportLab**: PDF generation with professional formatting
- **OpenPyXL**: Excel file creation with styling
- **CSV**: Standard CSV output for data interchange

### Web Framework
- **Flask**: Core web application framework
- **Werkzeug**: WSGI utilities and file handling
- **Bootstrap**: Frontend CSS framework

## Deployment Strategy

### Environment Configuration
- **Environment Variables**: API keys, configuration overrides
- **File Storage**: Local file system with configurable paths
- **Session Management**: Temporary session-based file handling

### Security Considerations
- **File Size Limits**: 10MB per file, 50 file maximum
- **File Type Validation**: Restricted to safe document formats
- **API Key Security**: Keys handled in memory, not persisted
- **Temporary File Cleanup**: Automatic cleanup of processed files

### Scalability Features
- **Batch Processing**: Efficient handling of multiple files
- **Memory Management**: Temporary file usage to minimize memory footprint
- **Error Isolation**: Individual file processing prevents cascade failures

### Production Readiness
- **Logging**: Comprehensive logging throughout the application
- **Error Handling**: Graceful error handling with user feedback
- **Configuration Management**: Environment-based configuration
- **Proxy Support**: WSGI proxy fix for deployment behind load balancers

## Development Notes

The application follows a modular architecture that separates concerns effectively. The AI provider system is designed to be extensible, allowing easy addition of new providers. The document processing pipeline is robust with individual file error handling. The report generation system provides professional output in multiple formats for business use.

The system is designed to handle real-world usage patterns with proper file size limits, error handling, and cleanup processes. The frontend provides a user-friendly interface for non-technical users while maintaining professional styling.