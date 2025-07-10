#!/usr/bin/env python3
"""
Teste simples para verificar se a aplicação está funcionando
"""
import sys
import os
import json
import tempfile
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Adicionar o diretório atual ao path
sys.path.insert(0, os.getcwd())

from document_processor import DocumentProcessor
from ai_providers import OpenAIClient

def create_test_image_with_text():
    """Cria uma imagem de teste com texto simulando um pedido de venda"""
    # Criar uma imagem branca
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Tentar usar uma fonte padrão
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Texto simulando um pedido de venda
    text_lines = [
        "PEDIDO DE VENDA #12345",
        "",
        "Cliente: Empresa Teste Ltda",
        "Data: 10/07/2024",
        "",
        "PRODUTOS:",
        "",
        "Cod: P001 | Parafuso M6x20 | Qtd: 100 | Valor Unit: R$ 0,50 | Total: R$ 50,00",
        "Cod: P002 | Arruela Lisa M6 | Qtd: 200 | Valor Unit: R$ 0,10 | Total: R$ 20,00", 
        "Cod: P003 | Porca M6 | Qtd: 100 | Valor Unit: R$ 0,30 | Total: R$ 30,00",
        "",
        "TOTAL GERAL: R$ 100,00"
    ]
    
    y_position = 50
    for line in text_lines:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 30
    
    # Salvar imagem temporária
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp_file.name)
    return temp_file.name

def test_document_processor():
    """Testa o processador de documentos"""
    print("🧪 Testando o processador de documentos...")
    
    # Criar processador
    processor = DocumentProcessor()
    
    # Criar imagem de teste
    test_image = create_test_image_with_text()
    print(f"✓ Imagem de teste criada: {test_image}")
    
    try:
        # Testar extração de texto
        text = processor._extract_text_from_image(test_image)
        print(f"✓ Texto extraído: {text[:100]}...")
        
        if "PEDIDO" in text and "Parafuso" in text:
            print("✓ OCR funcionando corretamente")
            return True
        else:
            print("❌ OCR não extraiu o texto esperado")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de OCR: {str(e)}")
        return False
    finally:
        # Limpar arquivo temporário
        try:
            os.unlink(test_image)
        except:
            pass

def test_json_parsing():
    """Testa o parsing de JSON"""
    print("\n🧪 Testando o parsing de JSON...")
    
    processor = DocumentProcessor()
    
    # Testar JSON válido
    valid_json = '{"produtos": [{"codigo": "P001", "descricao": "Teste", "quantidade": 10, "valor_unitario": 5.0, "valor_total": 50.0}]}'
    
    try:
        cleaned = processor._clean_json_response(valid_json)
        data = json.loads(cleaned)
        print("✓ JSON válido processado corretamente")
    except Exception as e:
        print(f"❌ Erro no JSON válido: {str(e)}")
        return False
    
    # Testar JSON com markdown
    markdown_json = '''```json
    {"produtos": [{"codigo": "P001", "descricao": "Teste", "quantidade": 10, "valor_unitario": 5.0, "valor_total": 50.0}]}
    ```'''
    
    try:
        cleaned = processor._clean_json_response(markdown_json)
        data = json.loads(cleaned)
        print("✓ JSON com markdown processado corretamente")
    except Exception as e:
        print(f"❌ Erro no JSON com markdown: {str(e)}")
        return False
    
    # Testar HTML (simulando erro)
    html_response = '<html><body>Error</body></html>'
    
    try:
        cleaned = processor._clean_json_response(html_response)
        data = json.loads(cleaned)
        if data.get('produtos') == []:
            print("✓ HTML tratado corretamente (retorna estrutura vazia)")
        else:
            print("❌ HTML não tratado corretamente")
            return False
    except Exception as e:
        print(f"❌ Erro no tratamento de HTML: {str(e)}")
        return False
    
    return True

def test_ai_prompt():
    """Testa se o prompt da IA está correto"""
    print("\n🧪 Testando prompt da IA...")
    
    # Simular um cliente OpenAI (sem fazer chamada real)
    try:
        # Apenas verificar se o prompt é gerado corretamente
        from ai_providers import OpenAIClient
        
        # Criar instância fictícia (não vai funcionar sem API key real)
        text_sample = "PEDIDO DE VENDA - Produto: Parafuso M6, Qtd: 100, Valor: R$ 50,00"
        
        # Verificar se conseguimos gerar o prompt
        client = OpenAIClient("fake-key", "gpt-4o")
        prompt = client._get_extraction_prompt(text_sample)
        
        if "JSON válido" in prompt and "produtos" in prompt:
            print("✓ Prompt da IA configurado corretamente")
            return True
        else:
            print("❌ Prompt da IA não contém as instruções corretas")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste do prompt: {str(e)}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes da aplicação...")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Teste 1: Processador de documentos
    if test_document_processor():
        tests_passed += 1
    
    # Teste 2: Parsing de JSON
    if test_json_parsing():
        tests_passed += 1
    
    # Teste 3: Prompt da IA
    if test_ai_prompt():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"🏁 Resultados: {tests_passed}/{total_tests} testes aprovados")
    
    if tests_passed == total_tests:
        print("✅ Todos os testes passaram! A aplicação está funcionando corretamente.")
        return True
    else:
        print("❌ Alguns testes falharam. Verifique os erros acima.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)