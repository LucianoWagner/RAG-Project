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
✅ Real-time chat with markdown support  
✅ Drag & drop PDF upload  
✅ Document management (list, delete, delete all)  
✅ Health monitoring (Ollama, Redis, MySQL)  
✅ Source attribution with relevance scores  
✅ Toast notifications  
✅ Loading states and error handling  
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

- `POST /auth/login`
- `POST /query`
- `POST /query/web-search`
- `POST /documents/upload`
- `GET /documents`
- `DELETE /documents/{filename}`
- `DELETE /documents/all`
- `GET /health`

## 🔐 Authentication

Default demo credentials (if using backend demo auth):
- Email: `admin@example.com`
- Password: `password`

## ✅ Status

**Build**: ✅ Successful  
**Type Check**: ✅ Passing  
**Linting**: ⚠️ CSS warnings (expected with Tailwind v4)

---

Built with ❤️ for the RAG PDF System
