# 📄 PDF Document Summarizer

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.2-blue)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Vercel](https://img.shields.io/badge/deployed-vercel-black)](https://vercel.com)

A production-ready web application that transforms lengthy PDF documents into concise, customizable summaries with **real-time streaming progress**. Built with FastAPI and React, featuring comprehensive testing, CI/CD, and enterprise-grade security.

📖 **[Documentation](docs/)** | 🚀 **[Quick Start](#-quick-start)** | 🏗️ **[Architecture](docs/ARCHITECTURE.md)**

---

## ✨ Features

### Core Functionality
- 📄 **PDF Text Extraction** - Intelligent text extraction using pdfplumber
- ✨ **AI Summarization** - Powered by Hugging Face BART model (facebook/bart-large-cnn)
- 🔄 **Real-time Streaming** - Server-Sent Events provide live progress updates
- 📊 **Live Progress Tracking** - Visual feedback through extraction, summarization, and formatting stages
- ⚙️ **Customizable Output**:
  - Length: Short (30-60 words), Medium (50-120 words), Long (80-200 words)
  - Tone: Neutral, Professional, or Casual

### User Experience
- 🎨 **Beautiful Dark UI** - "Technical elegance" design with smooth animations
- 💾 **Export Options** - Copy to clipboard, download as TXT or Markdown
- 📱 **Fully Responsive** - Optimized for desktop, tablet, and mobile
- ♿ **Accessible** - ARIA labels, keyboard navigation, screen reader support

### Production Ready
- 🔒 **Enterprise Security** - CORS, rate limiting, input validation, security headers
- 🧪 **Comprehensive Testing** - 91% backend coverage (37 tests), 93% frontend coverage (29 tests)
- 📈 **Error Tracking** - Sentry integration for production monitoring
- 📝 **Structured Logging** - JSON-formatted logs with request IDs
- 🎯 **Type Safety** - Pydantic validation and TypeScript throughout

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│   React     │  HTTP   │   FastAPI    │   API   │   Hugging Face  │
│  Frontend   │ ──────→ │   Backend    │ ──────→ │   BART Model    │
│  (Vercel)   │   SSE   │  (Vercel)    │  HTTPS  │   (Inference)   │
└─────────────┘ ←────── └──────────────┘         └─────────────────┘
                Real-time      ↓
                Progress    PDF Text
                           Extraction
```

### Backend Stack (FastAPI)
- **Async Operations** - httpx for non-blocking HTTP, run_in_executor for CPU-bound tasks
- **Streaming API** - Server-Sent Events for real-time progress updates
- **Pydantic Validation** - Type-safe request/response models
- **Structured Logging** - JSON logs with structlog
- **Rate Limiting** - slowapi protects API quotas (10 requests/hour default)
- **Security Headers** - XSS protection, CSP, clickjacking prevention

### Frontend Stack (React + TypeScript)
- **Real-time Progress** - Custom hook (`useStreamingSummarizer`) with EventSource
- **Component Architecture** - Modular design with separation of concerns
- **Framer Motion** - Smooth animations for state transitions
- **Type Safety** - Full TypeScript coverage with strict mode
- **Testing** - Vitest + Testing Library for components and hooks

### Deployment (Vercel)
- **Serverless Functions** - Python backend runs as serverless functions
- **Static Hosting** - React frontend served via global CDN
- **Environment-based Config** - Separate dev/preview/production environments
- **Automatic Deployments** - CI/CD via GitHub integration

**See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design.**

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ ([python.org](https://www.python.org/))
- Node.js 18+ ([nodejs.org](https://nodejs.org/))
- Hugging Face API token ([get one here](https://huggingface.co/settings/tokens))

### Installation

**1. Clone the repository**
```bash
git clone <your-repo-url>
cd document-summarizer
```

**2. Backend setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Add your HF_API_TOKEN to .env
```

**3. Frontend setup**
```bash
npm install
```

**4. Run locally**

Terminal 1 (Backend):
```bash
source venv/bin/activate
uvicorn api.summarize:app --reload --port 8000
```

Terminal 2 (Frontend):
```bash
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 🧪 Testing

### Run All Tests

```bash
# Backend tests (pytest)
source venv/bin/activate
pytest tests/ -v --cov=api

# Frontend tests (vitest)
npm run test:coverage

# Linting
make lint    # Backend (ruff + black)
npm run lint # Frontend (ESLint)
```

### Test Coverage

| Component | Coverage | Tests |
|-----------|----------|-------|
| Backend   | 91%      | 37    |
| Frontend  | 93.68%   | 29    |

**Coverage reports:**
- Backend: `htmlcov/index.html` (after running pytest with --cov)
- Frontend: `coverage/index.html` (after running `npm run test:coverage`)

---

## 🌐 Deployment

### Deploy to Vercel

**Option 1: Vercel CLI (Recommended)**

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Add environment variables
vercel env add HF_API_TOKEN  # Required
vercel env add SENTRY_DSN  # Optional (backend error tracking)
vercel env add VITE_SENTRY_DSN  # Optional (frontend error tracking)

# Deploy to production
vercel --prod
```

**Option 2: Vercel Dashboard (Auto-deployment)**

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Configure environment variables in dashboard:
   - `HF_API_TOKEN` (required)
   - `SENTRY_DSN` (optional)
   - `VITE_SENTRY_DSN` (optional)
4. Click "Deploy"
5. Vercel automatically deploys on every push to `main`

**Environment Variables:**

| Variable | Purpose | Required? |
|----------|---------|-----------|
| `HF_API_TOKEN` | Hugging Face API access | ✅ Yes |
| `SENTRY_DSN` | Backend error tracking | ⚠️ Optional |
| `VITE_SENTRY_DSN` | Frontend error tracking | ⚠️ Optional |

---

## 📁 Project Structure

```
document-summarizer/
├── api/                              # Backend (FastAPI)
│   ├── summarize.py                 # Main app with endpoints
│   ├── config.py                    # Environment configuration
│   ├── logger.py                    # Structured logging setup
│   ├── middleware.py                # Security headers
│   ├── models.py                    # Pydantic request/response models
│   ├── streaming.py                 # SSE event generator
│   └── utils/
│       ├── pdf_extractor.py        # Async PDF text extraction
│       ├── summarizer.py           # HF API integration + streaming
│       ├── formatter.py            # Text formatting (paragraphs)
│       └── usage_tracker.py        # API quota tracking
│
├── src/                             # Frontend (React + TypeScript)
│   ├── App.tsx                     # Main application component
│   ├── App.css                     # Design system and styles
│   ├── types.ts                    # TypeScript interfaces
│   ├── main.tsx                    # React entry point + Sentry
│   ├── components/
│   │   └── ProcessingProgress.tsx # Real-time progress UI
│   ├── hooks/
│   │   └── useStreamingSummarizer.ts # Streaming hook
│   └── utils/
│       ├── clipboard.ts            # Copy to clipboard
│       └── export.ts               # Download as TXT/Markdown
│
├── tests/                           # Backend tests (pytest)
│   ├── conftest.py                 # Test fixtures
│   ├── test_api.py                 # API endpoint tests
│   ├── test_summarizer.py          # Summarization logic tests
│   ├── test_pdf_extractor.py       # PDF extraction tests
│   └── test_formatter.py           # Text formatting tests
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md             # System design and decisions
│   └── API.md                      # Endpoint documentation
│
├── requirements.txt                 # Python dependencies
├── package.json                     # Node.js dependencies
├── vercel.json                      # Deployment configuration
├── pyproject.toml                   # Python tooling config
├── vitest.config.ts                # Frontend test config
├── vite.config.ts                  # Build configuration
└── README.md                        # This file
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose | Version |
|------------|---------|---------|
| FastAPI | Async web framework | 0.128+ |
| httpx | Async HTTP client | 0.25+ |
| pdfplumber | PDF text extraction | 0.10+ |
| Pydantic | Data validation | 2.0+ |
| structlog | Structured logging | 23.2+ |
| slowapi | Rate limiting | 0.1+ |
| sse-starlette | Server-Sent Events | 3.1+ |
| sentry-sdk | Error tracking | 2.0+ |
| pytest | Testing framework | 7.4+ |

### Frontend
| Technology | Purpose | Version |
|------------|---------|---------|
| React | UI framework | 18.2 |
| TypeScript | Type safety | 5.2 |
| Vite | Build tool | 5.0 |
| Framer Motion | Animations | 11.0 |
| Vitest | Testing framework | 4.0 |
| @sentry/react | Error tracking | Latest |

### Infrastructure
| Service | Purpose |
|---------|---------|
| Vercel | Hosting & serverless functions |
| Hugging Face | AI model inference API |
| Sentry | Error tracking & monitoring |
| GitHub Actions | CI/CD pipelines |

---

## 📖 API Documentation

### Endpoints

#### `POST /api/summarize`
Standard summarization (returns complete result after processing).

**Request:**
```typescript
{
  file: File (PDF),
  length_option: "Short" | "Medium" | "Long",
  tone_option: "Neutral" | "Professional" | "Casual"
}
```

**Response:**
```json
{
  "summary": "Raw summary text",
  "formatted_summary": "Summary with paragraph breaks",
  "extracted_text_preview": "First 500 characters...",
  "success": true,
  "metadata": {
    "original_word_count": 5000,
    "summary_word_count": 150,
    "compression_ratio": 0.03
  }
}
```

#### `POST /api/summarize-stream`
Streaming summarization with real-time progress updates via Server-Sent Events.

**Events:**
- `extraction_started` - PDF extraction beginning
- `extraction_complete` - Text extracted (includes word count)
- `chunk_processing` - Processing chunk N of M (includes progress %)
- `chunk_complete` - Chunk N summarized (includes partial summary)
- `formatting` - Formatting final summary
- `complete` - Final result ready
- `error` - Error occurred

#### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "PDF Summarizer API"
}
```

**See [docs/API.md](docs/API.md) for detailed API documentation.**

---

## 🔒 Security Features

The application implements multiple layers of security:

### Input Validation
- ✅ **Pydantic Models** - Type-safe validation for all inputs
- ✅ **File Type Checking** - Only accepts PDF files
- ✅ **File Size Limits** - Maximum 10MB per file
- ✅ **Content Validation** - Rejects PDFs with no extractable text

### Network Security
- ✅ **CORS Protection** - Environment-based origin whitelist (no wildcards)
- ✅ **Rate Limiting** - 10 requests/hour per IP (configurable)
- ✅ **Security Headers** - XSS protection, CSP, clickjacking prevention
- ✅ **HTTPS Only** - Enforced via Vercel

### Application Security
- ✅ **No PII Collection** - Sentry configured to exclude personal data
- ✅ **In-Memory Processing** - Files never written to disk
- ✅ **Environment Variables** - Secrets stored securely, never in code
- ✅ **Error Handling** - Sanitized error messages (no stack traces to users)

### Monitoring & Logging
- ✅ **Structured Logging** - JSON logs with request IDs
- ✅ **Error Tracking** - Sentry integration for production monitoring
- ✅ **Request Tracing** - Unique IDs for debugging
- ✅ **Usage Tracking** - Monthly quota monitoring for API limits

**See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for security architecture details.**

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Typical 5-page PDF | ~3-5 seconds |
| Streaming update frequency | Every 1-2 seconds |
| Max file size | 10MB |
| API timeout | 50 seconds (Vercel: 60s max) |
| Test coverage | >91% (backend + frontend) |
| Lighthouse score | 95+ (Performance, Accessibility) |

### Optimization Strategies

- **Async Processing** - Non-blocking I/O with httpx
- **Chunked Summarization** - 1000-char chunks for consistent quality
- **Real-time Feedback** - SSE prevents perceived slowness
- **Server-Side Rendering** - Fast initial page loads
- **CDN Delivery** - Global edge network via Vercel

---

## 🎨 Design System

The UI features a "**technical elegance**" aesthetic:

### Typography
- **Display** - Crimson Pro (editorial serif, 700 weight)
- **Body** - Manrope (geometric sans, 400-600 weights)
- **Monospace** - Courier New (extracted text preview)

### Color Palette
| Color | Hex | Usage |
|-------|-----|-------|
| Primary | `#00ADB5` | Teal accent for CTAs |
| Background | `#222831` | Dark gray base |
| Secondary | `#393E46` | Elevated surfaces |
| Text | `#EEEEEE` | Light gray content |

### Design Principles
- **Depth & Layering** - Subtle shadows and elevation
- **Purposeful Animation** - Smooth, meaningful transitions
- **Asymmetric Layout** - Visual interest without chaos
- **Accessible First** - WCAG AA compliant contrast ratios

---

## 🐛 Troubleshooting

### Common Issues

**"HF_API_TOKEN not set"**
```bash
# Check environment variable
echo $HF_API_TOKEN

# Set for current session
export HF_API_TOKEN=your_token_here

# Or add to .env file
echo "HF_API_TOKEN=your_token_here" >> .env
```

**"No text found in PDF"**
- PDF may be image-based (scanned document)
- Use OCR tool first (Adobe Acrobat, Tesseract)
- Verify PDF has selectable text

**Tests failing**
```bash
# Backend: Ensure pytest-asyncio is installed
pip install pytest-asyncio pytest-mock

# Frontend: Clear cache and reinstall
rm -rf node_modules coverage dist
npm install
npm run test:coverage
```

**Vercel deployment fails**
```bash
# Check logs
vercel logs <deployment-url>

# Verify environment variables
vercel env ls

# Ensure Python version is 3.9-3.11
# (Check vercel.json "runtime" setting)
```

**Rate limit exceeded**
- Default: 10 requests/hour per IP
- Adjust `RATE_LIMIT_PER_HOUR` in environment variables
- Or upgrade Hugging Face plan for more quota

**See [docs/API.md](docs/API.md) for API documentation and troubleshooting.**

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Ensure tests pass locally: `pytest tests/ -v && npm run test:coverage`
5. Run linting: `make lint && npm run lint`
6. Commit with descriptive message: `git commit -m "feat: add amazing feature"`
7. Push to your fork: `git push origin feature/amazing-feature`
8. Open a Pull Request

**Development Guidelines:**
- Add tests for new features (maintain >90% coverage)
- Follow existing code style (enforced by linters)
- Run tests locally before submitting PR
- Update documentation for API changes
- Use conventional commit messages (feat, fix, docs, chore, etc.)

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

This project is free to use for personal portfolios, learning, and commercial projects.

---

## 🙏 Acknowledgments

- **AI Model** - [Hugging Face](https://huggingface.co/) (facebook/bart-large-cnn)
- **PDF Extraction** - [pdfplumber](https://github.com/jsvine/pdfplumber)
- **UI Animations** - [Framer Motion](https://www.framer.com/motion/)
- **Hosting** - [Vercel](https://vercel.com/)
- **Error Tracking** - [Sentry](https://sentry.io/)

---

## 👤 Author

**Priyam Shah**
- 🐙 GitHub: [@priyamshah](https://github.com/priyamshah)
- 💼 LinkedIn: [Update with your LinkedIn]
- 📧 Email: [Update with your email]

---

## 📧 Contact & Support

- 🐛 **Bug Reports**: Open an issue on GitHub
- 💡 **Feature Requests**: Open an issue with "enhancement" label
- 📖 **Documentation**: [docs/](docs/)
- 💬 **Questions**: Open an issue with "question" label

---

<div align="center">

**⭐ Star this repo if you found it helpful!**

Made with ❤️ using FastAPI, React, and AI

</div>
