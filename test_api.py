"""
Test script para verificar el funcionamiento del sistema RAG.

Este script realiza pruebas básicas de los endpoints de la API.
Requiere que la aplicación esté ejecutándose en localhost:8000
"""

import requests
import json
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:8000"
TEST_PDF_PATH = "test_document.pdf"  # Cambiar por tu PDF de prueba


def print_header(text):
    """Imprime un header formateado."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def test_health():
    """Test del endpoint /health."""
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "healthy" and data["ollama_available"]:
                print("✅ Health check PASSED")
                return True
            else:
                print("⚠️  Health check WARNING: Some services not available")
                return False
        else:
            print("❌ Health check FAILED")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_upload(pdf_path):
    """Test del endpoint /documents/upload."""
    print_header("TEST 2: Document Upload")
    
    pdf_file = Path(pdf_path)
    
    if not pdf_file.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        print("Por favor, coloca un PDF de prueba en el directorio del proyecto")
        return False
    
    try:
        with open(pdf_file, 'rb') as f:
            files = {'file': (pdf_file.name, f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/documents/upload", files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            if data["chunks_processed"] > 0:
                print(f"✅ Upload PASSED - Processed {data['chunks_processed']} chunks")
                return True
            else:
                print("❌ Upload FAILED - No chunks processed")
                return False
        else:
            print(f"❌ Upload FAILED: {response.json().get('detail', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_query(question, should_have_context=True):
    """Test del endpoint /query."""
    print_header(f"TEST 3: Query - '{question}'")
    
    try:
        payload = {"question": question}
        response = requests.post(
            f"{BASE_URL}/query",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nAnswer: {data['answer']}")
            print(f"\nHas Context: {data['has_context']}")
            print(f"Sources Found: {len(data['sources'])}")
            
            if data['sources']:
                print("\nTop Source:")
                print(f"  Text: {data['sources'][0]['text'][:100]}...")
                print(f"  Score: {data['sources'][0]['score']:.4f}")
            
            if should_have_context:
                if data['has_context'] and len(data['sources']) > 0:
                    print("✅ Query PASSED - Found relevant context")
                    return True
                else:
                    print("❌ Query FAILED - No context found (expected to find)")
                    return False
            else:
                if not data['has_context']:
                    print("✅ Query PASSED - Correctly indicated no context")
                    return True
                else:
                    print("⚠️  Query WARNING - Found context when none expected")
                    return True
        else:
            print(f"❌ Query FAILED: {response.json().get('detail', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_tests():
    """Ejecuta todos los tests."""
    print("\n" + "█"*60)
    print("█  RAG PDF SYSTEM - TEST SUITE")
    print("█"*60)
    
    results = []
    
    # Test 1: Health
    results.append(("Health Check", test_health()))
    
    # Test 2: Upload
    if Path(TEST_PDF_PATH).exists():
        results.append(("Document Upload", test_upload(TEST_PDF_PATH)))
        
        # Test 3: Query con contexto
        results.append((
            "Query with Context",
            test_query("¿De qué trata el documento?", should_have_context=True)
        ))
        
        # Test 4: Query sin contexto
        results.append((
            "Query without Context",
            test_query("¿Quién ganó el mundial de fútbol 2022?", should_have_context=False)
        ))
    else:
        print(f"\n⚠️  Skipping upload and query tests - PDF not found: {TEST_PDF_PATH}")
        print("Para ejecutar todos los tests, coloca un PDF llamado 'test_document.pdf'")
    
    # Resumen
    print_header("RESULTADOS")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("█"*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    print("\nAsegúrate de que:")
    print("1. La aplicación esté ejecutándose (uvicorn app.main:app --reload)")
    print("2. Ollama esté ejecutándose (ollama serve)")
    print("3. Tengas un PDF de prueba llamado 'test_document.pdf'")
    
    input("\nPresiona Enter para comenzar los tests...")
    
    success = run_tests()
    
    if success:
        print("🎉 ¡Todos los tests pasaron exitosamente!")
    else:
        print("⚠️  Algunos tests fallaron. Revisa los errores arriba.")
