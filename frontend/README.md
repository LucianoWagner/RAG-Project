# Frontend - React Application

Modern, minimalist React frontend for the RAG PDF System.

## 🎨 Design

- **Style**: Modern black and white minimalist design
- **Font**: Inter from Google Fonts
- **Framework**: React 19 + TypeScript + Vite
- **UI Library**: Custom components with Tailwind CSS v4

## 🚀 Quick Start

### Prerequisites
- Node.js 20.19+ or 22.12+ recommended
- Backend running on `http://localhost:8000`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Opens on `http://localhost:3000`

### Production Build

```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
src/
├── app/               # App providers
├── features/          # Feature modules
│   ├── auth/         # Authentication
│   ├── chat/         # Chat interface
│   ├── documents/    # Document management
│   └── monitoring/   # Health monitoring
├── shared/           # Shared code
│   ├── components/   # Reusable UI components
│   ├── lib/         # Utilities, axios, query client
│   └── types/       # TypeScript types
└── pages/           # Route pages
```

## 🎯 Features

✅ JWT Authentication with auto-logout  
✅ **Real-time streaming chat (ChatGPT-style)** ⚡  
✅ Progressive text rendering word-by-word  
✅ Status messages during query processing  
✅ Markdown support in chat messages  
✅ Drag & drop PDF upload  
✅ Document management (list, delete, delete all)  
✅ Health monitoring (Ollama, Redis, MySQL)  
✅ Source attribution with relevance scores  
✅ Toast notifications  
✅ Loading states and error handling  
✅ **Stream cancellation** (Stop button)  
✅ Responsive design  

## 🔧 Tech Stack

- **React** 19.2.0 + **TypeScript** 5.9
- **Vite** 7.2.4 (build tool)
- **TanStack Query** 5.90 (server state)
- **Zustand** 5.0 (client state)
- **React Router** 7.13 (routing)
- **Tailwind CSS** 4.1 (styling)
- **Axios** 1.13 (HTTP client)
- **Framer Motion** 12.29 (animations)
- **React Markdown** 10.1 (markdown rendering)
- **React Dropzone** 14.4 (file upload)
- **Sonner** 2.0 (toasts)

## ⚙️ Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=RAG PDF System
```

## 📦 Build Output

```
dist/index.html                   0.46 kB │ gzip:   0.30 kB
dist/assets/index-DHX78UsV.css   16.54 kB │ gzip:   4.18 kB
dist/assets/index-BrBRenzP.js   655.95 kB │ gzip: 207.01 kB
```

## 🎨 UI Components

All components follow black/white design system:

- **Button**: 4 variants (default, outline, ghost, destructive)
- **Card**: Modular card components
- **Input**: Styled text input
- **Textarea**: Auto-resize textarea
- **LoadingSpinner**: Animated spinner

## 📡 API Endpoints

Configured to work with backend at `http://localhost:8000`:

### Authentication
- `POST /auth/login`

### Query Endpoints
- `POST /query` - Standard query (full response)
- `POST /query/web-search` - Wikipedia search (full response)
- **`GET /query/stream`** ⚡ - **Streaming query (progressive response)**
- **`GET /query/web-search/stream`** ⚡ - **Streaming Wikipedia (progressive)**

### Document Management
- `POST /documents/upload`
- `GET /documents`
- `DELETE /documents/{filename}`
- `DELETE /documents/all`

### Monitoring
- `GET /health`

## ⚡ Streaming Implementation

### Overview

The frontend uses **Server-Sent Events (SSE)** to receive progressive responses from the backend, similar to ChatGPT's streaming experience.

### Custom Hook: `useStreamingQuery`

**Location**: `src/features/chat/hooks/useStreamingQuery.ts`

**API**:
```typescript
const streaming = useStreamingQuery();

// Start streaming
await streaming.startStream(question, 'pdf' | 'web');

// Stop streaming
streaming.stopStream();

// State
streaming.isStreaming      // boolean
streaming.streamedContent  // accumulated text
streaming.sources          // source documents
streaming.statusMessage    // current status ("🔍 Analizando...")
streaming.error            // error message if any
streaming.suggestedAction  // suggested action (e.g., "web_search")
```

### SSE Event Handling

The hook parses SSE events from the backend:

| Event Type | Action |
|------------|--------|
| `status` | Update status message (e.g., "📚 Buscando...") |
| `sources` | Set source documents |
| `token` | Append token to content |
| `done` | Mark streaming as complete |
| `error` | Display error with suggested action |

**Implementation**:
```typescript
const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
let currentEventType = 'token';

while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    // Track current event type
    if (line.startsWith('event: ')) {
        currentEventType = line.slice(7).trim();
    }
    
    // Process data based on event type
    if (line.startsWith('data: ')) {
        const data = line.slice(6);
        switch (currentEventType) {
            case 'status': updateStatus(JSON.parse(data)); break;
            case 'sources': setSources(JSON.parse(data)); break;
            case 'token': appendContent(data); break;
            case 'done': finishStreaming(); break;
            case 'error': showError(JSON.parse(data)); break;
        }
    }
}
```

### UI Components

#### MessageBubble Updates

**Status Message Display**:
```tsx
{message.statusMessage && (
    <div className="text-sm text-muted-foreground mb-2">
        <LoadingSpinner size="sm" />
        {message.statusMessage}
    </div>
)}
```

**Streaming Cursor**:
```tsx
{message.isStreaming && message.content && (
    <span className="inline-block w-2 h-4 ml-1 bg-foreground animate-pulse">▊</span>
)}
```

#### ChatInput Stop Button

When streaming is active, the Send button transforms into a Stop button:

```tsx
{isLoading && onStop ? (
    <Button variant="destructive" onClick={onStop}>
        <Square className="h-4 w-4" />
    </Button>
) : (
    <Button type="submit" disabled={!input.trim() || isLoading}>
        <Send className="h-4 w-4" />
    </Button>
)}
```

### Stream Cancellation

Uses `AbortController` to cancel ongoing streams:

```typescript
const abortControllerRef = useRef<AbortController | null>(null);

// Start stream
abortControllerRef.current = new AbortController();
await fetch(url, { signal: abortControllerRef.current.signal });

// Cancel stream
const stopStream = () => {
    if (abortControllerRef.current) {
        abortControllerRef.current.abort();
    }
};
```

### Progressive UI Updates

The `ChatInterface` component updates the streaming message in real-time:

```typescript
useEffect(() => {
    setMessages((prev) =>
        prev.map((msg) =>
            msg.id === streamingMessageId
                ? {
                    ...msg,
                    content: streaming.error || streaming.streamedContent,
                    sources: streaming.sources,
                    statusMessage: streaming.statusMessage,
                    isStreaming: streaming.isStreaming,
                }
                : msg
        )
    );
}, [streaming.streamedContent, streaming.isStreaming, streaming.error]);
```

### Status Messages

The user sees these intermediate status updates:

| Phase | Message | Icon |
|-------|---------|------|
| Analyzing | "Analizando tu pregunta..." | 🔍 |
| Greeting | "Preparando saludo..." | 👋 |
| Searching | "Buscando en documentos..." | 📚 |
| Found | "Encontrados N fragmentos relevantes" | ✅ |
| Generating | "Generando respuesta..." | 🤖 |
| Wikipedia | "Buscando en Wikipedia..." | 🌐 |

### Performance Optimization

#### Health Check Polling

Health status polling runs every **15 minutes** to minimize backend load:

```typescript
// src/features/monitoring/hooks/useHealth.ts
refetchInterval: 900000 // 15 minutes
```

**Before**: 120 requests/hour (every 30s)  
**After**: 4 requests/hour (every 15min) ✅

## 🔐 Authentication

Default demo credentials (if using backend demo auth):
- Email: `admin@example.com`
- Password: `password`

## ✅ Status

**Build**: ✅ Successful  
**Type Check**: ✅ Passing  
**Linting**: ⚠️ CSS warnings (expected with Tailwind v4)  
**Streaming**: ✅ Fully functional

---

Built with ❤️ for the RAG PDF System
