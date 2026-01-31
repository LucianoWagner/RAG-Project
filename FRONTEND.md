# Frontend - React Application

## 🎨 Modern, Minimalist UI

Tech Stack: React 19.2 + TypeScript + Vite + Tailwind CSS + TanStack Query

### Key Features

#### 1. Authentication 🔐
- JWT-based with auto-logout on 401
- Protected routes
- Token persistence

#### 2. Tool Selector 🔧
Switch between search modes:
- **📄 PDF Documents** → `POST /query`
- **🌐 Web Search** → `POST /query/web-search`

#### 3. Suggested Action Buttons 💡
Interactive prompts when bot suggests actions:
- **NO_DOCUMENTS**: [📤 Subir PDF] [🌐 Buscar en Internet]
- **LOW_RELEVANCE**: [🌐 Buscar en Internet]

#### 4. Chat Interface 💬
- Markdown support
- Auto-scroll
- Source attribution
- Confidence scores

#### 5. Document Management 📁
- Drag & drop upload
- Duplicate detection
- Delete all

#### 6. Health Monitoring 🏥
Real-time status:
- 🟢 Ollama
- 🟢 Redis
- 🟢 MySQL
- 🟢 Vector Store

### Setup

```bash
cd frontend
npm install
npm run dev  # http://localhost:3000
```

**Environment (.env):**
```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=RAG PDF System
```

### User Flows

**First-Time User (No Documents):**
1. Ask question → NO_DOCUMENTS
2. Click "Subir PDF" OR "Buscar en Internet"

**Document Query:**
1. Upload PDFs
2. Select "PDF Documents" mode
3. Ask question → Get answer with sources

### Recent Improvements ✨

- **Quick Relevance Check**: 80% faster for irrelevant queries
- **DB Cleanup**: Delete All now clears MySQL table
- **Health Status Fix**: Shows correct service states
