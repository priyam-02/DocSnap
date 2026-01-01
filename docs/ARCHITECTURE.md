# System Architecture

This document provides an in-depth look at the PDF Document Summarizer's architecture, design decisions, and technical implementation.

## Table of Contents

1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Data Flow](#data-flow)
6. [Security Architecture](#security-architecture)
7. [Deployment Architecture](#deployment-architecture)
8. [Design Decisions](#design-decisions)
9. [Performance Optimizations](#performance-optimizations)
10. [Scalability Considerations](#scalability-considerations)

---

## System Overview

The PDF Document Summarizer is a full-stack web application built using a modern, serverless architecture optimized for Vercel deployment.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  React SPA (Vite)                                       │   │
│  │  • TypeScript components                                │   │
│  │  • Framer Motion animations                             │   │
│  │  • EventSource for SSE                                  │   │
│  │  • Sentry error tracking                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/SSE
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  FastAPI (ASGI)                                         │   │
│  │  • Async request handling                               │   │
│  │  • Pydantic validation                                  │   │
│  │  • Rate limiting (slowapi)                             │   │
│  │  • Structured logging (structlog)                      │   │
│  │  • Sentry error tracking                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
      ↓                    ↓                    ↓
┌──────────┐      ┌─────────────┐      ┌──────────────┐
│   PDF    │      │  Hugging    │      │   Storage    │
│ Plumber  │      │   Face API  │      │  (In-Memory) │
│          │      │             │      │              │
│  Local   │      │  External   │      │    Local     │
└──────────┘      └─────────────┘      └──────────────┘
```

### Request Flow

1. **Client uploads PDF** → Drag-and-drop or file picker
2. **Frontend validates** → File type, size, format
3. **API receives file** → Multipart form data
4. **PDF extraction** → pdfplumber extracts text (async)
5. **Text chunking** → Split into 1000-char segments
6. **AI summarization** → Send chunks to HuggingFace BART
7. **Formatting** → Group sentences into paragraphs
8. **Response** → Return formatted summary with metadata

For **streaming** requests (SSE), progress events are emitted at each stage.

---

## Technology Stack

### Backend Decisions

| Technology | Why Chosen | Alternatives Considered |
|------------|------------|------------------------|
| **FastAPI** | Modern async framework, automatic OpenAPI docs, Pydantic integration | Flask (no async), Django (too heavy) |
| **httpx** | Async HTTP client for HF API calls | requests (blocking), aiohttp (more complex) |
| **pdfplumber** | Reliable text extraction, handles complex layouts | PyPDF2 (limited), pdfminer (complex) |
| **Pydantic** | Type-safe validation, automatic serialization | marshmallow (more boilerplate), attrs |
| **sse-starlette** | Simple SSE implementation for FastAPI | WebSockets (overkill), polling (inefficient) |
| **structlog** | JSON logging, contextual information | standard logging (unstructured), loguru |
| **slowapi** | Easy rate limiting with decorators | Flask-Limiter (Flask-specific), custom implementation |

### Frontend Decisions

| Technology | Why Chosen | Alternatives Considered |
|------------|------------|------------------------|
| **React** | Component model, rich ecosystem, team familiarity | Vue (smaller ecosystem), Svelte (less mature) |
| **TypeScript** | Type safety, better DX, catches bugs early | JavaScript (no types), Flow (less popular) |
| **Vite** | Fast dev server, modern build tool, HMR | Create React App (slower), Webpack (complex config) |
| **Framer Motion** | Declarative animations, great API | React Spring (imperative), CSS animations (limited) |
| **Vitest** | Fast, Vite integration, modern API | Jest (slower), Mocha (less integrated) |

---

## Backend Architecture

### Directory Structure

```
api/
├── summarize.py          # Main FastAPI app, endpoints, middleware
├── config.py             # Environment-based configuration (Pydantic)
├── logger.py             # Structured logging setup (structlog)
├── middleware.py         # Security headers middleware
├── models.py             # Pydantic request/response schemas
├── streaming.py          # SSE event generator for real-time progress
└── utils/
    ├── pdf_extractor.py  # Async PDF text extraction
    ├── summarizer.py     # HuggingFace API integration + streaming
    ├── formatter.py      # Text formatting (paragraph grouping)
    └── usage_tracker.py  # Monthly API quota tracking
```

### Key Components

#### 1. FastAPI Application (`summarize.py`)

```python
# Middleware stack (order matters):
1. CORS (allow specific origins)
2. RequestID (add unique ID to each request)
3. SecurityHeaders (XSS, CSP, etc.)
4. Rate Limiting (slowapi, 10 req/hour)

# Endpoints:
GET  /api/health           # Health check
POST /api/summarize        # Standard (blocking) summarization
POST /api/summarize-stream # Streaming with SSE
```

**Design choice**: Two endpoints instead of one with query parameter
- **Pros**: Clear separation, different response types, easier to test
- **Cons**: Slight code duplication
- **Verdict**: Worth it for clarity and type safety

#### 2. Async PDF Extraction (`utils/pdf_extractor.py`)

```python
async def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    # Wrap pdfplumber (blocking) in executor
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _extract_text_sync, file_bytes)
```

**Why async?**
- pdfplumber is CPU-bound (blocking)
- `run_in_executor` moves it to thread pool
- Keeps event loop responsive for other requests
- Essential for serverless (limited concurrency)

#### 3. Summarization Logic (`utils/summarizer.py`)

**Chunking Strategy:**
```python
chunk_size = 1000  # characters
chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
```

**Why 1000 characters?**
- BART max input: 1024 tokens (~1200 chars)
- Leaves room for tone instruction prefix
- Small enough to avoid truncation, large enough to maintain context

**Streaming Implementation:**
```python
async def summarize_text_streaming(text, length, tone) -> AsyncIterator[dict]:
    async with httpx.AsyncClient() as client:
        for i, chunk in enumerate(chunks):
            yield {"type": "chunk_start", "chunk_index": i}
            response = await client.post(HF_API_URL, ...)
            yield {"type": "chunk_complete", "summary": result}
```

**Design choice**: Sequential vs Parallel Processing
- **Current**: Sequential (one chunk at a time)
- **Alternative**: Parallel (all chunks simultaneously)
- **Trade-off**:
  - Sequential: Respects rate limits, predictable progress, lower memory
  - Parallel: Faster (3x speedup), but can hit rate limits, harder to track progress
- **Verdict**: Sequential for free tier, parallel possible with Pro

#### 4. Rate Limiting (`config.py` + `summarize.py`)

```python
@limiter.limit(f"{settings.RATE_LIMIT_PER_HOUR}/hour")
async def summarize_endpoint(...):
```

**Why rate limit?**
1. **API Quota Protection**: HF free tier = 30K chars/month
2. **DoS Prevention**: Single user can't monopolize service
3. **Cost Control**: Prevents unexpected bills
4. **Fair Usage**: Ensures availability for all users

**Implementation choices**:
- Per-IP limiting (not per-user, simpler)
- Configurable via environment variable
- Custom error handler with helpful messages

---

## Frontend Architecture

### Directory Structure

```
src/
├── main.tsx                          # Entry point, Sentry init
├── App.tsx                           # Main component (file upload, options, results)
├── App.css                           # Design system, all styles
├── types.ts                          # TypeScript interfaces
├── components/
│   └── ProcessingProgress.tsx       # Progress bar with animated stages
├── hooks/
│   └── useStreamingSummarizer.ts    # SSE consumption, state management
└── utils/
    ├── clipboard.ts                  # Copy to clipboard (with fallback)
    └── export.ts                     # Download as TXT/Markdown
```

### State Management

**Decision**: No external state library (Redux, Zustand, etc.)

**Rationale**:
- App state is simple (upload, processing, result)
- Single source of truth in `useStreamingSummarizer` hook
- Parent-child prop passing sufficient
- Adds complexity without benefit for this scale

**State shape:**
```typescript
type AppState = {
  file: File | null;
  lengthOption: LengthOption;
  toneOption: ToneOption;
  processingState: {
    stage: 'idle' | 'extracting' | 'summarizing' | 'formatting' | 'complete' | 'error';
    message: string;
    progress: number;  // 0-100
    partialSummary?: string;
  };
  result: SummarizeResponse | null;
  error: string | null;
};
```

### Streaming Architecture

**Custom Hook Pattern:**
```typescript
function useStreamingSummarizer() {
  const [processingState, setProcessingState] = useState(...)

  const summarizeStreaming = useCallback(async (file, options) => {
    const response = await fetch('/api/summarize-stream', ...)
    const reader = response.body.getReader()

    // Parse SSE events
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      // Update state based on event type
      handleSSEEvent(event)
    }
  }, [])

  return { processingState, result, error, summarizeStreaming }
}
```

**Why custom hook?**
- Encapsulates complex SSE logic
- Reusable across components
- Testable in isolation
- Clear API (single responsibility)

### Component Architecture

**Decision**: Component-per-feature, not atomic design

**Structure**:
```
App.tsx (container)
├── FileUploadZone
├── OptionsPanel
├── ProcessingProgress (component/)
└── ResultsDisplay
```

**Why not atomic design?**
- Overkill for small app (3 pages worth of UI)
- Atomic = atoms/molecules/organisms/templates/pages
- Current structure is "just right" (Goldilocks principle)
- Easy to refactor later if needed

---

## Data Flow

### Standard Summarization Flow

```
1. User uploads PDF
   ├─→ Frontend validates (size, type)
   └─→ FormData with file + options

2. POST /api/summarize
   ├─→ FastAPI receives multipart form
   ├─→ Pydantic validates length/tone
   └─→ Rate limiter checks quota

3. PDF Extraction
   ├─→ run_in_executor(pdfplumber.extract)
   ├─→ Validate text exists
   └─→ Track usage (quota)

4. Summarization
   ├─→ Split into chunks (1000 chars)
   ├─→ For each chunk:
   │   ├─→ Add tone instruction
   │   ├─→ POST to HuggingFace API
   │   └─→ Append summary
   └─→ Concatenate chunks

5. Formatting
   ├─→ Split on sentence boundaries
   ├─→ Group every 3 sentences
   └─→ Join with double newlines

6. Response
   ├─→ SummarizeResponse model
   └─→ Include metadata (word counts, compression)
```

### Streaming Flow (SSE)

```
1. User uploads PDF
   └─→ POST /api/summarize-stream

2. Backend opens EventSourceResponse
   └─→ Yields events as processing happens

3. Events emitted:
   ├─→ extraction_started
   ├─→ extraction_complete (with word count)
   ├─→ chunk_processing (progress %)
   ├─→ chunk_complete (partial summary)
   ├─→ formatting
   └─→ complete (final result)

4. Frontend consumes:
   ├─→ EventSource listens
   ├─→ Updates processingState on each event
   ├─→ Displays progress bar
   └─→ Shows partial summaries
```

**Why SSE over WebSockets?**
- Unidirectional (server → client only)
- Simpler protocol (HTTP, not TCP)
- Built-in reconnection
- Works through proxies/firewalls
- Perfect fit for progress updates

---

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────┐
│  1. Client-Side Validation               │
│     • File type check (PDF only)        │
│     • File size check (<10MB)           │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  2. Network Security                     │
│     • CORS (origin whitelist)           │
│     • HTTPS only (Vercel)               │
│     • Security headers (CSP, XSS)       │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  3. Application Layer                    │
│     • Pydantic validation               │
│     • Rate limiting (10/hour)           │
│     • Input sanitization                │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  4. Processing Layer                     │
│     • In-memory only (no disk writes)   │
│     • Timeout protection (50s)          │
│     • Error sanitization                │
└───────────────┬─────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  5. Monitoring & Logging                 │
│     • Structured logs (no PII)          │
│     • Sentry error tracking             │
│     • Request tracing (unique IDs)      │
└─────────────────────────────────────────┘
```

### Threat Model

| Threat | Mitigation |
|--------|------------|
| **XSS** | Content-Security-Policy header, React auto-escaping |
| **CSRF** | SameSite cookies, CORS origin check (no cookies currently) |
| **DoS** | Rate limiting (10 req/hour), file size limit (10MB) |
| **Injection** | Pydantic validation, no SQL (serverless), no shell commands |
| **File Upload Attacks** | Type validation, size limit, in-memory processing |
| **API Abuse** | Rate limiting, quota tracking, IP-based throttling |
| **Data Leakage** | No persistence, in-memory only, sanitized errors |

---

## Deployment Architecture

### Vercel Serverless

```
┌─────────────────────────────────────────────────────────┐
│                    Vercel Global CDN                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  US East     │  │   Europe     │  │  Asia Pacific│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ↓                   ↓                   ↓
┌─────────────┐   ┌─────────────────┐   ┌────────────┐
│  Static     │   │  Serverless     │   │  Edge      │
│  Frontend   │   │  Functions      │   │  Config    │
│  (dist/)    │   │  (Python API)   │   │  (routing) │
└─────────────┘   └─────────────────┘   └────────────┘
```

### Serverless Functions (Backend)

**Configuration** (`vercel.json`):
```json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.11",
      "memory": 3008,        // Max (needed for pdfplumber)
      "maxDuration": 60      // Pro tier (Hobby = 10s)
    }
  }
}
```

**Why serverless?**
- **Cost**: Pay per execution, not idle time
- **Scaling**: Automatic, handles traffic spikes
- **Maintenance**: No servers to manage
- **Geographic**: Runs close to users (CDN)

**Limitations**:
- **Cold start**: First request ~500ms slower
  - Mitigated: Vercel keeps warm functions hot
- **Execution time**: 60s max (Pro), 10s (Hobby)
  - Mitigated: Timeout protection at 50s
- **Memory**: 3008MB max
  - Mitigated: In-memory processing, no large buffers

---

## Design Decisions

### 1. Why Not Load Model Locally?

**Original** (Streamlit app):
```python
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
# Model size: ~1.6GB
```

**Problem**:
- Vercel deployment limit: 250MB (Hobby), 1GB (Pro)
- Cold start: ~30s to load model
- Memory: 2-3GB required

**Solution**: Hugging Face Inference API
- Model hosted externally
- Zero deployment size impact
- Cold start: ~200ms (network only)
- Cost: Free tier (30K chars/month), Pro ($9/month for 10M chars)

**Trade-offs**:
| Aspect | Local Model | HF API |
|--------|-------------|--------|
| Deployment Size | ❌ 1.6GB | ✅ 0 bytes |
| Cold Start | ❌ 30s | ✅ 200ms |
| Latency | ✅ 50ms | ⚠️ 200-500ms |
| Cost | ✅ Free | ⚠️ $9/mo (Pro) |
| Rate Limits | ✅ None | ❌ 30K chars/mo (free) |

**Verdict**: HF API for portfolio/demo, consider local for production at scale.

### 2. Why Sequential Chunking?

**Current**: Process chunks one at a time
**Alternative**: Process all chunks in parallel with `asyncio.gather()`

**Trade-offs**:
```python
# Sequential
for chunk in chunks:
    summary = await summarize_chunk(chunk)

# Parallel
summaries = await asyncio.gather(*[summarize_chunk(c) for c in chunks])
```

| Aspect | Sequential | Parallel |
|--------|------------|----------|
| Speed | ❌ Slow (N * latency) | ✅ Fast (~latency) |
| Rate Limits | ✅ Respects limits | ❌ Easily exceeded |
| Progress Tracking | ✅ Clear (N of M) | ⚠️ Complex |
| Memory | ✅ Low (1 at a time) | ❌ High (N at once) |
| Error Handling | ✅ Simple | ⚠️ Complex |

**Verdict**: Sequential for free tier simplicity, parallel is 1-line change if needed.

### 3. Why Dark Theme Only?

**Current**: Single dark theme
**Alternative**: Light/dark toggle with theme context

**Rationale**:
- **Brand**: "Technical elegance" = dark aesthetic
- **Scope**: Theme switcher = +4 hours implementation
- **Value**: Marginal (personal preference, not core feature)
- **Portfolio**: Demonstrates design vision (dark = choice, not limitation)

**If adding later**:
```typescript
// Would need:
1. ThemeContext provider
2. CSS variable swapping
3. Toggle UI component
4. localStorage persistence
```

---

## Performance Optimizations

### Backend

1. **Async I/O**: All HTTP calls use `httpx.AsyncClient`
2. **Thread Pool**: CPU-bound PDF extraction in executor
3. **Streaming Responses**: SSE reduces perceived latency
4. **Timeout Protection**: 50s limit prevents zombie processes
5. **Chunking**: 1000-char chunks optimize BART performance

### Frontend

1. **Code Splitting**: Vite automatically splits chunks
2. **Lazy Loading**: Framer Motion only loaded when needed
3. **Memoization**: React.memo on ProcessingProgress
4. **Debouncing**: File validation debounced (300ms)
5. **CDN**: Static assets served from Vercel Edge

### Deployment

1. **Serverless Functions**: Scale to zero, pay per use
2. **Edge Caching**: Static assets cached globally
3. **Compression**: Gzip/Brotli for all responses
4. **HTTP/2**: Enabled by default on Vercel

---

## Scalability Considerations

### Current Capacity

| Metric | Current | At Scale |
|--------|---------|----------|
| Requests/day | ~100 | 10,000+ |
| PDFs/day | ~50 | 5,000+ |
| Avg processing time | 5s | 5s |
| Concurrent users | 10 | 100+ |

### Bottlenecks

1. **HuggingFace API Rate Limit**
   - Free: 30K chars/month (~12 PDFs)
   - Solution: Upgrade to Pro ($9/mo = 10M chars)

2. **Vercel Serverless Concurrency**
   - Free: 10 concurrent executions
   - Solution: Upgrade to Pro (100+ concurrent)

3. **Memory (3008MB per function)**
   - Current: Sufficient
   - Solution: Optimize pdfplumber usage if needed

### Horizontal Scaling

**Current architecture already supports**:
- ✅ Stateless (no sessions)
- ✅ Serverless (auto-scaling)
- ✅ CDN (global distribution)
- ✅ No database (no bottleneck)

**Would need for 10K+ daily users**:
1. **Caching**: Redis for frequent PDFs (deduplication)
2. **Queue**: Background processing for long documents
3. **CDN**: Cloudflare for additional edge caching
4. **Monitoring**: DataDog/New Relic for performance metrics

---

## Monitoring & Observability

### Logging Strategy

**Structured JSON logs**:
```json
{
  "event": "pdf_extracted",
  "request_id": "uuid",
  "text_length": 5000,
  "word_count": 800,
  "filename": "document.pdf",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Tracking (Sentry)

**Captured**:
- Unhandled exceptions
- HTTP 5xx errors
- Slow API calls (>5s)
- Failed summarizations

**Not Captured** (filtered):
- User errors (400s)
- Rate limit hits (429s)
- Personally identifiable information

### Key Metrics

1. **Request Rate**: Requests per minute
2. **Error Rate**: Errors per 100 requests
3. **P95 Latency**: 95th percentile response time
4. **Quota Usage**: HF API characters consumed
5. **Success Rate**: % of successful summarizations

---

## Future Enhancements

### Short-term (< 1 month)

1. **Summary History**: localStorage cache of past summaries
2. **Comparison Mode**: Side-by-side different length/tone options
3. **PDF Download**: Export summary as formatted PDF (jspdf)
4. **Keyboard Shortcuts**: Power user features (↑ for options, ⌘K for upload)

### Medium-term (1-3 months)

1. **User Accounts**: Save summaries to cloud (Supabase)
2. **Batch Processing**: Upload multiple PDFs at once
3. **Custom Models**: Allow users to choose summarization model
4. **API Keys**: Public API for developer access

### Long-term (3+ months)

1. **OCR Support**: Scan image-based PDFs (Tesseract)
2. **Multi-language**: Support non-English documents
3. **Embeddings**: Semantic search across summary history
4. **Mobile App**: React Native iOS/Android app

---

## Conclusion

The PDF Document Summarizer demonstrates modern full-stack development practices:

- ✅ **Async-first**: Non-blocking I/O throughout
- ✅ **Type-safe**: Pydantic (backend) + TypeScript (frontend)
- ✅ **Production-ready**: Security, testing, monitoring
- ✅ **Scalable**: Serverless architecture supports growth
- ✅ **Maintainable**: Clear separation of concerns, well-documented

The architecture balances:
- **Simplicity** - No over-engineering, right-sized solutions
- **Performance** - Async, streaming, caching where it matters
- **Security** - Defense in depth, multiple validation layers
- **Cost** - Serverless reduces operational expenses

**Key Takeaway**: Architecture serves the product, not the other way around.
