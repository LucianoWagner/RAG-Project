# 🛡️ Resilience Patterns - Implementation Guide

## ✅ Patrones Aplicados

Los siguientes patrones de resilience se aplicaron siguiendo las mejores prácticas de la industria:

---

## 1️⃣ LLM Service (`app/services/llm_service.py`)

### `generate_answer()` - Respuestas principales

```python
@with_timeout(30)
@with_retry(max_attempts=3, min_wait=1, max_wait=5)
@with_circuit_breaker(ollama_breaker)
async def generate_answer(question, context):
    ...
```

**Stack de protección:**
1. **Circuit Breaker**: Si Ollama falla 5 veces consecutivas → fail-fast por 60s
2. **Retry**: Hasta 3 intentos con backoff exponencial (1s, 2s, 4s)
3. **Timeout**: Cancela si excede 30 segundos

**Beneficio**: 
- Evita esperar 30s por cada falla cuando Ollama está caído
- Recuperación automática de errores transitorios
- Protección contra requests que se cuelgan

---

### `generate_greeting_response()` - Saludos

```python
@with_timeout(15)
@with_retry(max_attempts=2, min_wait=1, max_wait=3)
@with_circuit_breaker(ollama_breaker)
async def generate_greeting_response(greeting_text):
    ...
```

**Diferencias con generate_answer:**
- Timeout más corto (15s vs 30s) - los saludos deben ser rápidos
- Menos reintentos (2 vs 3) - menos crítico que respuestas
- **Comparte circuit breaker** con `generate_answer` (importante!)

---

## 2️⃣ Web Search Service (`app/services/web_search_service.py`)

### `search()` - Búsqueda en Wikipedia

```python
@with_timeout(20)
@with_retry(max_attempts=2, min_wait=1, max_wait=3, exceptions=(Exception,))
def search(query, max_results=3):
    ...
```

**Protección:**
- Timeout: 20s máximo (Wikipedia debe responder rápido)
- Retry: 2 intentos para errores de red

**Por qué Exception genérico:**
- Wikipedia API puede lanzar múltiples tipos de errores
- Mejor capturar todo y reintentar

---

### `search_and_summarize()` - Búsqueda + LLM

```python
@with_timeout(60)
async def search_and_summarize(question, max_results=2):
    ...
```

**Solo timeout:**
- 60s total (20s Wikipedia + 30s LLM + buffer)
- No retry porque ya tiene fallback interno (raw snippets)

---

## 3️⃣ Database (`app/database/database.py`)

### `init_database()` - Inicialización

```python
@with_retry(
    max_attempts=3,
    min_wait=2,
    max_wait=10,
    exceptions=(OperationalError, DBAPIError)
)
async def init_database():
    ...
```

**Por qué:**
- MySQL puede no estar listo al inicio (Docker startup)
- Retry con backoff largo (2s, 4s, 8s) da tiempo a MySQL
- Solo reintenta errores de conexión, no errores de schema

---

### `check_database_health()` - Health check

```python
@with_retry(
    max_attempts=2,
    min_wait=1,
    max_wait=3,
    exceptions=(OperationalError,)
)
async def check_database_health():
    ...
```

**Menos agresivo:**
- Solo 2 intentos (es un health check, no crítico)
- Backoff más corto (1s, 2s)

---

## 📊 Configuración por Servicio

| Servicio | Timeout | Retry Attempts | Backoff | Circuit Breaker |
|----------|---------|----------------|---------|-----------------|
| **LLM Answer** | 30s | 3 | 1s→2s→4s | ✅ (5 fails, 60s) |
| **LLM Greeting** | 15s | 2 | 1s→2s | ✅ (shared) |
| **Wikipedia Search** | 20s | 2 | 1s→2s | ❌ |
| **Wikipedia Summary** | 60s | ❌ | - | ❌ |
| **DB Init** | ∞ | 3 | 2s→4s→8s | ❌ |
| **DB Health** | ∞ | 2 | 1s→2s | ❌ |

---

## 🎯 Flujo de Ejemplo: Query con Ollama caído

### Sin resilience:
```
Request 1 → Ollama timeout (30s) → Error 500
Request 2 → Ollama timeout (30s) → Error 500
Request 3 → Ollama timeout (30s) → Error 500
...
Total time wasted: 90s+
```

### Con resilience:
```
Request 1 → Ollama FAIL → retry (wait 1s) → FAIL → retry (wait 2s) → FAIL
           Total: 33s, fail_count=1

Request 2 → Ollama FAIL → retry → FAIL → retry → FAIL
           Total: 33s, fail_count=2

...

Request 5 → Ollama FAIL → retry → FAIL → retry → FAIL
           Total: 33s, fail_count=5

🔴 Circuit Breaker OPENS

Request 6 → Circuit breaker OPEN → Error 503 (0s) ⚡
Request 7 → Circuit breaker OPEN → Error 503 (0s) ⚡
...

After 60s → Circuit breaker HALF_OPEN
Request N → Tries again...
  Success? → Circuit CLOSED ✅
  Fail?    → Circuit OPEN again ❌
```

**Tiempo ahorrado**: Requests 6+ son instantáneos en lugar de 30s cada uno

---

## 🔍 Monitoreo

### Ver estado de Circuit Breakers

**Endpoint**: `GET /health`

```json
{
  "services": {
    "ollama": {
      "available": true,
      "circuit_breaker": "closed"  // closed, open, half_open
    }
  }
}
```

**En código**:
```python
from app.utils.resilience import get_circuit_breaker_status

status = get_circuit_breaker_status()
# {
#   "ollama": {
#     "state": "closed",
#     "fail_counter": 0,
#     "opened_at": None
#   }
# }
```

---

## 🧪 Testear Resilience

### 1. Apagar Ollama

```bash
# Detener Ollama
docker stop ollama  # o ctrl+c si corre local

# Hacer query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "test"}'

# Primera vez: 3 retries (33s total)
# Quinta vez: Circuit breaker abre → instant error ⚡
```

### 2. Latencia alta

```bash
# Simular latencia de red (Linux/Mac)
sudo tc qdisc add dev eth0 root netem delay 5000ms

# Request debería cancelarse por timeout
```

### 3. MySQL caído

```bash
# Detener MySQL
docker-compose stop mysql

# Health check
curl http://localhost:8000/health
# "mysql": {"available": false}  ← después de 2 retries

# Levantar MySQL
docker-compose start mysql

# Health check auto-recupera
```

---

## 🎛️ Configuración en `.env`

```bash
# Circuit Breaker
CIRCUIT_BREAKER_THRESHOLD=5      # Abre después de N fallas
CIRCUIT_BREAKER_TIMEOUT=60       # Reintenta después de N segundos

# Timeouts
OLLAMA_TIMEOUT=30                # LLM timeout (segundos)

# Retries
OLLAMA_RETRY_ATTEMPTS=3          # Número de reintentos
```

---

## ⚠️ Importante: Orden de Decorators

**SIEMPRE este orden**:
```python
@with_timeout(30)      # 1. Outer: Timeout general
@with_retry(...)       # 2. Middle: Retry logic
@with_circuit_breaker  # 3. Inner: Fail-fast check
async def function():
    ...
```

**¿Por qué?**
1. Timeout envuelve todo (incluye retries)
2. Retry envuelve la función real
3. Circuit breaker checks ANTES de ejecutar

**Orden incorrecto** ❌:
```python
@with_circuit_breaker  # Si está afuera, timeout no aplica
@with_timeout(30)      
@with_retry(...)       
async def function():
    ...
```

---

## 📚 Referencias

- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html) - Martin Fowler
- [Exponential Backoff](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) - AWS
- [Resilience4j](https://resilience4j.readme.io/) - Java library (inspiración)
- [Polly](https://github.com/App-vNext/Polly) - .NET library (inspiración)

---

## ✅ Resumen

**Antes**: Servicios externos fallen → App crashea o cuelga  
**Ahora**: Servicios externos fallan → App se degrada gracefully

**Beneficios**:
- ⚡ Fail-fast cuando servicios están caídos (circuit breaker)
- 🔄 Auto-recuperación de errores transitorios (retry)
- ⏱️ Protección contra requests colgados (timeout)
- 📊 Monitoreo del estado de servicios externos
