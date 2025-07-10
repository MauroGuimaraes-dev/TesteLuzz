#!/usr/bin/env python3
"""
Teste final do sistema para verificar se os erros foram corrigidos
"""
import sys
import os
sys.path.insert(0, '.')

from document_processor import DocumentProcessor

def test_html_response_handling():
    """Testa o tratamento de respostas HTML"""
    processor = DocumentProcessor()
    
    # Simular resposta HTML (erro comum)
    html_response = '<html><body><h1>Error 401: Unauthorized</h1><p>Invalid API key</p></body></html>'
    
    try:
        # Testar limpeza
        cleaned = processor._clean_json_response(html_response)
        print(f"✓ HTML response handled: {cleaned}")
        
        # Testar parsing
        products = processor._parse_ai_response(html_response, "test.pdf")
        print(f"✓ HTML parsing result: {len(products)} products")
        
        return True
    except Exception as e:
        print(f"❌ Error handling HTML: {str(e)}")
        return False

def test_json_response_handling():
    """Testa o tratamento de respostas JSON válidas"""
    processor = DocumentProcessor()
    
    # JSON válido
    valid_json = '{"produtos": [{"codigo": "P001", "descricao": "Teste", "quantidade": 10, "valor_unitario": 5.0, "valor_total": 50.0}]}'
    
    try:
        products = processor._parse_ai_response(valid_json, "test.pdf")
        print(f"✓ Valid JSON handled: {len(products)} products")
        
        if len(products) == 1 and products[0]['descricao'] == 'Teste':
            print("✓ Product data correctly extracted")
            return True
        else:
            print("❌ Product data not correctly extracted")
            return False
    except Exception as e:
        print(f"❌ Error handling valid JSON: {str(e)}")
        return False

def test_error_patterns():
    """Testa detecção de padrões de erro"""
    processor = DocumentProcessor()
    
    error_responses = [
        "Error: insufficient quota",
        "Unable to process request",
        "Quota exceeded for this account",
        "Invalid API key provided",
        "<!DOCTYPE html><html>Error</html>"
    ]
    
    for response in error_responses:
        try:
            cleaned = processor._clean_json_response(response)
            if cleaned == '{"produtos": []}':
                print(f"✓ Error pattern detected: {response[:30]}...")
            else:
                print(f"❌ Error pattern NOT detected: {response[:30]}...")
                return False
        except Exception as e:
            print(f"❌ Exception handling error pattern: {str(e)}")
            return False
    
    return True

def main():
    """Executa todos os testes"""
    print("🧪 Teste Final - Verificação de Robustez")
    print("=" * 50)
    
    tests = [
        ("HTML Response Handling", test_html_response_handling),
        ("JSON Response Handling", test_json_response_handling),
        ("Error Pattern Detection", test_error_patterns)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        if test_func():
            passed += 1
            print(f"✅ {test_name} - PASSOU")
        else:
            print(f"❌ {test_name} - FALHOU")
    
    print("\n" + "=" * 50)
    print(f"🏁 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 SISTEMA ROBUSTO - Pronto para uso!")
        print("✓ Não desperdiçará mais créditos com erros de HTML")
        print("✓ Tratamento adequado de erros de API")
        print("✓ Parsing JSON resiliente")
    else:
        print("⚠️  Ainda há problemas que precisam ser corrigidos")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)