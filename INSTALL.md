# Guía Rápida de Instalación

## Windows

### 1. Clonar/Descargar el proyecto
```bash
cd "e:\Proyecto IA\rag-pdf-system"
```

### 2. Ejecutar script de setup
```powershell
.\setup.ps1
```

### 3. Instalar Ollama (si no está instalado)
- Descargar desde: https://ollama.ai
- Ejecutar instalador
- Abrir terminal y ejecutar:
```bash
ollama pull mistral:7b
```

### 4. Iniciar Ollama
```bash
ollama serve
```

### 5. Iniciar la aplicación
```bash
# En otra terminal, dentro del proyecto:
venv\Scripts\activate
uvicorn app.main:app --reload
```

### 6. Abrir documentación
Navegar a: http://localhost:8000/docs

---

## Linux/Mac

### 1. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Instalar Ollama
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull mistral:7b
```

### 4. Iniciar servicios
```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: FastAPI
uvicorn app.main:app --reload
```

---

## Verificación

### Health Check
```bash
curl http://localhost:8000/health
```

Debe retornar:
```json
{
  "status": "healthy",
  "ollama_available": true,
  "embedding_model_loaded": true,
  "vector_store_initialized": true
}
```

### Subir PDF de prueba
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@tu_documento.pdf"
```

### Realizar consulta
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿De qué trata el documento?"}'
```

---

## Troubleshooting

**Error: "Ollama is not available"**
- Verificar que `ollama serve` esté ejecutándose
- Verificar que el puerto 11434 esté libre

**Error: "No text could be extracted"**
- Verificar que el PDF contenga texto extraíble (no sea solo imagen)

**Lentitud en primera ejecución**
- Normal: descarga del modelo de embeddings (~80MB)
- Solo ocurre la primera vez

---

Para más información, ver: [README.md](README.md)
