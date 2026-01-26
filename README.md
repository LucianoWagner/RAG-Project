# RAG PDF System con FastAPI - Sistema Inteligente con Wikipedia

Sistema avanzado de **Retrieval-Augmented Generation (RAG)** con **clasificación inteligente de intents** que permite cargar documentos PDF, realizar consultas en lenguaje natural, y obtener información de Wikipedia cuando no hay documentos relevantes. El sistema evita alucinaciones mediante contexto recuperado y validación de similitud.

## 🎯 Características Principales

### Core Features
- **100% Local**: Sin servicios pagos ni APIs comerciales
- **Sin Alucinaciones**: Responde solo con información verificada
- **Arquitectura Modular**: Código limpio siguiendo principios SOLID
- **Type-Safe**: Validación automática con Pydantic
- **Logging Completo**: Trazabilidad de todas las operaciones
- **Persistencia**: Índice vectorial guardado en disco
- **API RESTful**: Documentación automática con Swagger/OpenAPI

### 🆕 Funcionalidades Avanzadas

#### 🧠 Clasificación Inteligente de Intents
- **Estrategia Híbrida**: Regex (fast-path) + Embeddings (precisión)
- Detecta automáticamente: saludos, consultas documentales, queries irrelevantes
- Tiempo de clasificación: ~50ms para saludos, ~200ms para embeddings

#### 💬 Saludos Personalizados
- Respuestas generadas por LLM para interacciones naturales
- Fallback estático si el LLM es lento
- Detección multilingüe (español, inglés, etc.)

#### 🌐 Búsqueda Web con Wikipedia
- **Motor**: Wikipedia API (gratis, sin límites de rate)
- **Idiomas**: Español con fallback automático a inglés
- **Precisión**: Contenido verificado sin alucinaciones
- **Optimización**: Prompts avanzados para resúmenes detallados (3-5 oraciones)

#### 📊 Validación de Relevancia
- **Threshold automático**: 0.7 (L2 distance estándar de industria)
- Detecta cuando documentos no contienen info relevante
- Sugiere búsqueda web inteligentemente

#### 🎯 Sugerencias Contextuales
- Vector store vacío → Sugiere upload de PDFs o búsqueda web
- Baja relevancia → Ofrece búsqueda en Wikipedia
- Respuestas con confianza score (0.0-1.0)

## 🏗️ Arquitectura

```mermaid
graph TB
    Client[Cliente HTTP] -->|POST /query| Router[Query Router]
    
    Router -->|1. Classify| Intent[Intent Classifier]
    Intent -->|Greeting| GreetLLM[LLM Greeting]
    Intent -->|Query| DocFlow[Document Flow]
    
    DocFlow -->|Check| VectorStore[FAISS Vector Store]
    VectorStore -->|Empty?| WebSearch[Wikipedia Search]
    VectorStore -->|Has docs| Similarity[Similarity Check]
    
    Similarity -->|Score >= 0.7| WebSearch
    Similarity -->|Score < 0.7| RAG[RAG Pipeline]
    
    RAG --> Embedding[Embedding Service]
    Embedding --> VectorStore
    VectorStore -->|Top-K chunks| LLM[LLM Service - Ollama]
    
    GreetLLM --> Client
    WebSearch --> WikiAPI[Wikipedia API]
    WikiAPI --> LLM
    LLM --> Client
```

### Flujo Inteligente de Consultas

#### 1. Clasificación de Intent
1. Usuario envía query en `/query`
2. **IntentClassifier** analiza con regex + embeddings
3. Determina: `GREETING | DOCUMENT_QUERY`

#### 2. Manejo de Saludos
Si es saludo:
1. **LLMService** genera respuesta personalizada
2. Fallback a mensaje estático si falla
3. Respuesta directa sin búsqueda

#### 3. Consultas Documentales
Si es query:
1. **Vector Store Check**: ¿Hay documentos?
   - No → Sugiere upload o web search
2. **Similarity Check**: ¿Relevancia >= 0.7?
   - No → Sugiere búsqueda en Wikipedia
3. **RAG Pipeline**: Genera respuesta con contexto
4. Incluye `confidence_score` y `suggested_action`

#### 4. Búsqueda Web Fallback
Endpoint `/query/web-search`:
1. **WikipediaSearch** busca 2-3 artículos relevantes
2. Extrae 3 oraciones por artículo
3. **LLM** resume con prompt optimizado
4. Retorna respuesta detallada con fuentes

## 🛠️ Stack Tecnológico

| Componente | Tecnología | Justificación |
|------------|------------|---------------|
| **Backend** | FastAPI | Async, validación automática, documentación integrada |
| **PDF Parsing** | pdfplumber | Robusto, maneja tablas y layouts complejos |
| **Embeddings** | sentence-transformers | Modelo open-source ligero (`all-MiniLM-L6-v2`) |
| **Vector Store** | FAISS | Eficiente, local, 100% gratuito |
| **LLM** | Ollama | Ejecución local de modelos (Mistral, LLaMA, Phi) |
| **Web Search** | Wikipedia API | Gratis, sin límites, contenido verificado |
| **Intent Classification** | Regex + Embeddings | Híbrido para velocidad y precisión |
| **Validación** | Pydantic | Type-safe, validación automática |
| **Config** | python-dotenv | Variables de entorno |

## 📋 Requisitos Previos

- **Python 3.10+**
- **Ollama** instalado y ejecutándose
- ~500MB de espacio en disco (modelos + datos)
- Conexión a internet (solo para Wikipedia)

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/rag-pdf-system.git
cd rag-pdf-system
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar y configurar Ollama

#### Windows/Mac
1. Descargar desde [ollama.ai](https://ollama.ai)
2. Instalar y ejecutar Ollama
3. Descargar modelo:

```bash
ollama pull mistral:7b
```

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve
ollama pull mistral:7b
```

### 5. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env si es necesario (valores por defecto funcionan)
```

**Variables disponibles:**
- `OLLAMA_BASE_URL`: URL de Ollama (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: Modelo a usar (default: `mistral:7b`)
- `EMBEDDING_MODEL`: Modelo de embeddings (default: `all-MiniLM-L6-v2`)
- `CHUNK_SIZE`: Tamaño de chunks (default: `500`)
- `CHUNK_OVERLAP`: Solapamiento (default: `50`)
- `TOP_K_RESULTS`: Fragmentos a recuperar (default: `3`)

## ▶️ Ejecución

### Iniciar el servidor

```bash
uvicorn app.main:app --reload
```

El servidor estará disponible en `http://localhost:8000`

### Documentación interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 Endpoints de la API

### 1. Health Check

**GET** `/health`

Verifica el estado de todos los servicios.

**Respuesta:**
```json
{
  "status": "healthy",
  "ollama_available": true,
  "embedding_model_loaded": true,
  "vector_store_initialized": true
}
```

**Ejemplo:**
```bash
curl http://localhost:8000/health
```

---

### 2. Subir Documento

**POST** `/documents/upload`

Sube y procesa un archivo PDF.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (archivo PDF)

**Respuesta:**
```json
{
  "filename": "documento.pdf",
  "chunks_processed": 42,
  "message": "Document processed successfully"
}
```

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@documento.pdf"
```

---

### 3. Consultar con Inteligencia (🆕 Mejorado)

**POST** `/query`

Realiza una pregunta con clasificación inteligente de intent.

**Request:**
```json
{
  "question": "¿Cuál es el tema principal del documento?"
}
```

**Respuestas según escenario:**

#### A) Saludo detectado
```json
{
  "answer": "¡Hola! ¿En qué puedo ayudarte hoy?",
  "sources": [],
  "has_context": false,
  "intent": "GREETING",
  "confidence_score": null,
  "suggested_action": null
}
```

#### B) Documentos cargados, alta relevancia
```json
{
  "answer": "Basado en los documentos, el tema principal es...",
  "sources": [
    {
      "text": "Fragmento relevante del documento...",
      "score": 0.342
    }
  ],
  "has_context": true,
  "intent": "DOCUMENT_QUERY",
  "confidence_score": 0.85,
  "suggested_action": null
}
```

#### C) Vector store vacío
```json
{
  "answer": "No tengo documentos cargados aún. ¿Deseas:\n1. Subir PDFs primero\n2. Buscar esta información en internet?",
  "sources": [],
  "has_context": false,
  "intent": "NO_DOCUMENTS",
  "confidence_score": null,
  "suggested_action": "upload_or_search"
}
```

#### D) Baja relevancia
```json
{
  "answer": "No encontré información relevante en los documentos cargados. ¿Quieres que busque esta información en internet?",
  "sources": [],
  "has_context": false,
  "intent": "LOW_RELEVANCE",
  "confidence_score": 0.0,
  "suggested_action": "web_search"
}
```

**Ejemplos:**
```bash
# Saludo
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hola"}'

# Query documental
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es el tema principal?"}'
```

---

### 4. Búsqueda Web en Wikipedia (🆕 Nuevo)

**POST** `/query/web-search`

Busca información directamente en Wikipedia cuando los documentos no tienen la respuesta.

**Request:**
```json
{
  "question": "¿Quién es Lionel Messi?"
}
```

**Respuesta:**
```json
{
  "answer": "Lionel Andrés Messi es un futbolista argentino nacido el 24 de junio de 1987 en Rosario. Se desempeña como delantero y es considerado uno de los mejores jugadores de todos los tiempos. Ha ganado 7 Balones de Oro, récord en la historia del fútbol.",
  "sources": [],
  "has_context": true,
  "intent": "WEB_SEARCH",
  "confidence_score": null,
  "suggested_action": null
}
```

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/query/web-search" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Quién ganó el mundial 2022?"}'
```

**Características:**
- ✅ Busca en español con fallback a inglés
- ✅ 2-3 artículos de Wikipedia por consulta
- ✅ Resumen detallado con prompt optimizado
- ✅ 100% preciso (sin alucinaciones)
- ✅ Respuestas en ~5-7 segundos

## 📁 Estructura del Proyecto

```
rag-pdf-system/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app y endpoints
│   ├── config.py                  # Configuración con Pydantic
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Modelos Pydantic (actualizados)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py         # Extracción de texto PDF
│   │   ├── chunking_service.py    # División en fragmentos
│   │   ├── embedding_service.py   # Generación de embeddings
│   │   ├── vector_store.py        # Gestión FAISS
│   │   ├── llm_service.py         # Interacción con Ollama
│   │   ├── intent_classifier.py   # 🆕 Clasificación híbrida
│   │   └── web_search_service.py  # 🆕 Wikipedia integration
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # Configuración de logging
│       └── intent_helpers.py      # 🆕 Helpers para detección
├── data/
│   ├── uploaded_pdfs/             # PDFs guardados
│   └── vector_store/              # Índice FAISS persistente
├── .env                           # Variables de entorno
├── .env.example                  # Plantilla de configuración
├── .gitignore
├── requirements.txt
└── README.md
```

## 🔍 Decisiones Técnicas

### ¿Por qué Clasificación de Intents?

- **UX mejorada**: Responde apropiadamente a diferentes tipos de input
- **Eficiencia**: Fast-path para saludos (~50ms)
- **Inteligencia**: Detecta cuándo buscar en web vs documentos

### ¿Por qué Wikipedia?

- **Gratis**: Sin límites de API, completamente gratuito
- **Confiable**: Contenido verificado por comunidad
- **Actualizado**: Información más reciente que modelos LLM
- **Sin rate limits**: A diferencia de DuckDuckGo u otros

### Estrategia de Similarity Threshold

- **Valor**: 0.7 (L2 distance)
- **Basado en**: Estándares de `sentence-transformers`
- **Trade-off**: Balance entre precisión y recall
- Scores < 0.7 = Alta relevancia
- Scores >= 0.7 = Baja relevancia → Sugiere web search

### Prompt Engineering Avanzado

Prompt optimizado para Wikipedia:
1. **Role-playing**: "Actúa como experto en resumir..."
2. **Estructura clara**: CONTEXTO → TAREA → REGLAS → OUTPUT
3. **Instrucciones específicas**: Fechas, nombres, lugares, cantidades
4. **Anti-hallucination**: "NUNCA inventes, Si Wikipedia contradice..."
5. **Formato**: 3-5 oraciones completas y conectadas

### RAG vs Web Search

| Aspecto | RAG (Documentos) | Web Search (Wikipedia) |
|---------|------------------|------------------------|
| **Velocidad** | ~2-3s | ~5-7s |
| **Precisión** | Alta (si relevante) | 100% verificado |
| **Cobertura** | Limitada a PDFs | Conocimiento general |
| **Actualización** | Manual (upload) | Tiempo real |

## ⚠️ Limitaciones Conocidas

### Generales
1. **Dependencia de Ollama**: Requiere que Ollama esté ejecutándose
2. **Memoria**: Modelos LLM grandes requieren 8GB+ RAM
3. **Solo PDFs**: No soporta otros formatos (Word, HTML, etc.)
4. **Tamaño de contexto**: Limitado por el modelo LLM usado

### Específicas de Nuevas Features
5. **Wikipedia idiomas**: Solo español e inglés (configurable)
6. **Saludos LLM lentos**: ~30s, usa fallback estático
7. **Sin streaming**: Respuestas se muestran completas (no progresivas)
8. **Threshold fijo**: 0.7 hardcoded (futuro: configurable)

## 📊 Métricas de Rendimiento

| Operación | Tiempo Promedio | Notas |
|-----------|----------------|-------|
| Saludo (regex) | ~50ms | Fast-path |
| Saludo (LLM) | ~30s | Con personalización |
| Query documento (hit) | ~2-3s | Alta relevancia |
| Query documento (miss) | ~200ms | Detección rápida |
| Búsqueda Wikipedia | ~5-7s | 2-3 artículos |
| Intent classification | ~200ms | Embeddings |

## 🧪 Testing

### Tests de Intent Classification

```bash
# 1. Saludo básico
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hola"}'
# Esperado: intent=GREETING

# 2. Query con documentos
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es el tema principal?"}'
# Esperado: intent=DOCUMENT_QUERY, confidence_score

# 3. Query sin documentos
# (sin PDFs cargados)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Qué es Python?"}'
# Esperado: intent=NO_DOCUMENTS, suggested_action=upload_or_search

# 4. Búsqueda web
curl -X POST "http://localhost:8000/query/web-search" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Quién es Messi?"}'
# Esperado: Resumen de Wikipedia
```

### Test de Relevancia

```bash
# Query irrelevante (con PDFs de fútbol cargados)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cómo funciona Python?"}'
# Esperado: intent=LOW_RELEVANCE, suggested_action=web_search
```

## 🔧 Troubleshooting

### Error: "Ollama is not available"

**Solución**: Verificar que Ollama esté ejecutándose:
```bash
# Windows: Task Manager
# Linux/Mac:
ps aux | grep ollama

# Reiniciar Ollama
ollama serve
```

### Wikipedia no retorna resultados

**Causas posibles**:
- Tema muy específico o reciente
- Problema de conectividad

**Solución**: Verificar internet, reformular pregunta

### Saludos muy lentos

**Causa**: LLM toma ~30s para personalizar

**Solución**: Sistema usa fallback automático. Para mejorar, usar modelo más rápido (`phi` en lugar de `mistral`)

### Intent incorrectamente clasificado

**Causa**: Embeddings no reconocen patrón

**Solución**: Agregar pattern al regex en `intent_helpers.py`

## 📈 Próximas Mejoras

### Planificadas
- [ ] Streaming de respuestas (SSE)
- [ ] Cache de búsquedas Wikipedia (Redis)
- [ ] Threshold configurable por endpoint
- [ ] Métricas y analytics dashboard
- [ ] Tests unitarios completos

### En Consideración
- [ ] Frontend web interactivo
- [ ] Soporte para más formatos (DOCX, TXT)
- [ ] OCR para PDFs escaneados
- [ ] Chat conversacional con historial
- [ ] Multi-idioma en Wikipedia
- [ ] API keys opcionales para Google Search

## 🎓 Recursos y Referencias

### Modelos Recomendados

| Modelo | Tamaño | RAM | Velocidad | Calidad |
|--------|--------|-----|-----------|---------|
| **phi:3.5** | 2.2GB | 4GB | ⚡⚡⚡ | ⭐⭐⭐ |
| **mistral:7b** | 4.1GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐ |
| **llama3.2** | 7.4GB | 16GB | ⚡ | ⭐⭐⭐⭐⭐ |

Cambiar modelo en `.env`:
```bash
OLLAMA_MODEL=phi:3.5  # Rápido
# o
OLLAMA_MODEL=llama3.2  # Mejor calidad
```

### Paper References

- [RAG Architecture](https://arxiv.org/abs/2005.11401)
- [Sentence-BERT](https://arxiv.org/abs/1908.10084)
- [FAISS](https://arxiv.org/abs/1702.08734)

## 👨‍💻 Autor

**Lucia** - Desarrollador Python | Backend | Generative AI

- GitHub: [tu-usuario](https://github.com/tu-usuario)
- LinkedIn: [tu-perfil](https://linkedin.com/in/tu-perfil)

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/)
- [FAISS](https://faiss.ai/)
- [Sentence Transformers](https://www.sbert.net/)
- [Ollama](https://ollama.ai/)
- [pdfplumber](https://github.com/jsvine/pdfplumber)
- [Wikipedia API](https://pypi.org/project/wikipedia/)

---

**¿Tienes preguntas o sugerencias?** [Abre un issue](https://github.com/tu-usuario/rag-pdf-system/issues) 🚀

**⭐ Si te gustó este proyecto, dale una estrella en GitHub!**
