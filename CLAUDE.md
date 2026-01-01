# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A production-ready PDF document summarizer deployed on Vercel with a FastAPI backend and React frontend. Users upload PDFs and receive customizable summaries with adjustable length (Short/Medium/Long) and tone (Neutral/Professional/Casual).

## Architecture Overview

### Stack
- **Backend**: FastAPI (Python 3.9+) with async endpoints
- **Frontend**: React 18 + TypeScript + Vite
- **Deployment**: Vercel (serverless functions for Python, static hosting for React)
- **AI**: Hugging Face Inference API (facebook/bart-large-cnn model)

### Critical Architectural Decision: Why HF API?

**Problem**: The original Streamlit app loaded `facebook/bart-large-cnn` (~1.6GB) locally, which exceeds Vercel's deployment limits (250MB Hobby, 1GB Pro).

**Solution**: Migrated to Hugging Face Inference API to:
- Eliminate model from deployment bundle (zero size impact)
- Avoid cold start delays from model loading
- Leverage HF's infrastructure for model optimization
- Use free tier (30K chars/month) sufficient for portfolio/demo usage

**Trade-off**: Added network latency (~200-500ms) and rate limits, but necessary for Vercel deployment.

## Running the Application

### Development (Local)

**Backend:**
```bash
source venv/bin/activate
export HF_API_TOKEN=your_token_here
uvicorn api.summarize:app --reload --port 8000
```

**Frontend:**
```bash
npm install
npm run dev  # Runs on http://localhost:5173
```

Vite dev server proxies `/api/*` requests to `http://localhost:8000` (configured in [vite.config.ts](vite.config.ts)).

### Production (Vercel)

```bash
vercel env add HF_API_TOKEN  # One-time setup
vercel --prod
```

## Backend Architecture ([api/](api/))

### File Structure

```
api/
├── summarize.py          # FastAPI app with /api/summarize and /api/health endpoints
└── utils/
    ├── pdf_extractor.py  # Async PDF→text extraction using pdfplumber
    ├── summarizer.py     # HF API integration for BART summarization
    └── formatter.py      # Paragraph formatting (groups every 3 sentences)
```

### Key Implementation Details

**1. PDF Extraction ([api/utils/pdf_extractor.py](api/utils/pdf_extractor.py))**
- Uses `BytesIO` for in-memory processing (serverless compatible)
- No files written to disk (Vercel functions are ephemeral)
- Adapted from original Streamlit `extract_text_from_pdf()` function

**2. Summarization ([api/utils/summarizer.py](api/utils/summarizer.py))**
- Replaces local `transformers.pipeline()` with HTTP API calls to HF
- **Chunking strategy** (unchanged from original):
  - 1000-character chunks, no overlap
  - Sequential processing (not parallelized to avoid rate limits)
  - Each chunk gets tone instruction prepended before summarization
- **Length control** via BART's `max_length`/`min_length` parameters:
  - Short: 30-60 tokens
  - Medium: 50-120 tokens
  - Long: 80-200 tokens
- **Tone implementation**: Prompt engineering, not model fine-tuning
  - Different instruction prefixes for each tone
  - "Summarize..." (Neutral) | "Write a formal..." (Professional) | "Explain in a friendly..." (Casual)

**3. Formatting ([api/utils/formatter.py](api/utils/formatter.py))**
- **Direct copy** from original Streamlit app (lines 19-30 of old app.py)
- Groups every 3 sentences into paragraphs using regex splitting
- Enhances readability of concatenated chunk summaries

**4. FastAPI Endpoint ([api/summarize.py](api/summarize.py))**

**POST /api/summarize**
- Accepts multipart form data (file + length_option + tone_option)
- **Validations**:
  - File type: PDF only (.pdf extension check)
  - File size: Max 10MB
  - Content: Rejects PDFs with no extractable text
- **Timeout**: 50s (stays under Vercel's 60s function limit)
- **Error handling**: Comprehensive try-catch with specific HTTP exceptions
  - 400: Bad request (invalid file, too large, no text)
  - 504: Timeout (document too large)
  - 500: Server errors (HF API issues, missing token)

**GET /api/health**
- Simple health check for monitoring

### Dependencies ([requirements.txt](requirements.txt))

**Removed from original**: `streamlit`, `transformers`, `torch` (eliminated ~2GB of dependencies)

**Added**: `fastapi`, `python-multipart`, `requests`, `uvicorn`

**Kept**: `pdfplumber` (PDF text extraction)

## Frontend Architecture ([src/](src/))

### File Structure

```
src/
├── App.tsx        # Main application component (all logic and UI)
├── App.css        # Complete styling and design system
├── types.ts       # TypeScript interfaces for API and state
├── main.tsx       # React entry point
└── vite-env.d.ts  # Vite type definitions
```

### Design System

**Theme** (CSS variables in [App.css](src/App.css)):
- Primary: #00ADB5 (teal) - inherited from original Streamlit config
- Background: #222831 (dark gray)
- Secondary: #393E46 (elevated gray)
- Text: #EEEEEE (light gray)

**Typography**:
- Display/headings: **Crimson Pro** (editorial serif) - 700 weight for titles
- Body text: **Manrope** (geometric sans) - 400-600 weights
- Monospace: Courier New for extracted text preview

**Design Philosophy**: "Technical elegance"
- Combines editorial typography with developer tool precision
- Dark theme with depth (shadows, layering)
- Animated grid background
- Framer Motion for smooth state transitions

### Key Components (All in App.tsx)

**State Management**:
- Single `useState<AppState>` hook manages entire application state
- No external state library needed (app is simple enough)

**File Upload**:
- Drag-and-drop zone with visual feedback (`isDragging` state)
- Click-to-browse fallback
- File validation before accepting
- Display file info with remove button

**Summary Display**:
- AnimatePresence for enter/exit animations
- Staggered paragraph reveals (0.1s delay between each)
- Collapsible extracted text preview

**Error Handling**:
- Toast-style error messages with icons
- Animated height transitions
- Cleared on successful submission

### API Integration

**Fetch call** in `handleSummarize()`:
- Creates FormData with file + options
- Posts to `/api/summarize`
- Handles response/error states
- Updates UI based on result

**Proxy setup** ([vite.config.ts](vite.config.ts)):
```typescript
proxy: {
  '/api': 'http://localhost:8000'
}
```
In development, Vite forwards `/api/*` to FastAPI. In production, Vercel routes handle this.

## Deployment Configuration ([vercel.json](vercel.json))

**Critical settings**:

1. **Builds**:
   - `@vercel/python` for `api/**/*.py` (serverless functions)
   - `@vercel/static-build` for React frontend (dist/ folder)

2. **Routes**:
   - `/api/*` → Python functions
   - `/*` → Static build (dist/)

3. **Functions config**:
   - `memory: 3008` - Maximum memory (required for pdfplumber + larger PDFs)
   - `maxDuration: 60` - Max timeout (Pro tier, Hobby is 10s)

4. **Environment variables** (set via Vercel dashboard or CLI):
   - `HF_API_TOKEN` - Required for summarization

## Code Reuse from Original Streamlit App

**Original app.py location**: Kept in repo root for reference

**Direct reuse (no modifications)**:
1. `format_summary_to_paragraphs()` → [api/utils/formatter.py](api/utils/formatter.py)
2. Length settings dict → [api/utils/summarizer.py](api/utils/summarizer.py) (LENGTH_SETTINGS)
3. Tone instructions dict → [api/utils/summarizer.py](api/utils/summarizer.py) (TONE_INSTRUCTIONS)

**Modified (minor changes)**:
1. `extract_text_from_pdf()` → [api/utils/pdf_extractor.py](api/utils/pdf_extractor.py)
   - Added BytesIO wrapper for in-memory processing
   - Made async for FastAPI compatibility

**Completely rewritten**:
1. `summarize_text()` → [api/utils/summarizer.py](api/utils/summarizer.py)
   - Replaced `transformers.pipeline()` with `requests.post()` to HF API
   - Same chunking logic, different execution method
2. Streamlit UI → [src/App.tsx](src/App.tsx) + [src/App.css](src/App.css)
   - Complete React rewrite with TypeScript
   - Maintained feature parity (upload, length, tone, summary display, text preview)

## Common Development Tasks

### Adding a new summary length option:

1. Add to LENGTH_SETTINGS in [api/utils/summarizer.py](api/utils/summarizer.py)
2. Update type in [src/types.ts](src/types.ts) (`LengthOption`)
3. Add `<option>` in [src/App.tsx](src/App.tsx) length dropdown

### Changing summarization model:

1. Update `HF_API_URL` in [api/utils/summarizer.py](api/utils/summarizer.py)
2. Adjust parameter mappings if new model has different API
3. Test chunking strategy compatibility

### Modifying UI theme:

1. Update CSS variables in [src/App.css](src/App.css) (`:root` section)
2. Colors: `--color-*`
3. Fonts: `--font-*`
4. Spacing/shadows: `--shadow-*`, `--radius-*`

### Testing backend locally without frontend:

```bash
curl -X POST http://localhost:8000/api/summarize \
  -F "file=@test.pdf" \
  -F "length_option=Medium" \
  -F "tone_option=Neutral"
```

## Known Constraints & Considerations

**HF API Free Tier Limits**:
- 30,000 input characters/month
- For a 5-page PDF (~2,500 chars), that's ~12 documents/month
- Upgrade to HF Pro ($9/month) for 10M chars if needed

**Vercel Function Limits**:
- Hobby: 10s timeout, 1024MB memory (insufficient for this app)
- Pro: 60s timeout, 3008MB memory (required)
- Consider implementing client-side progress tracking for long documents

**PDF Extraction Limitations**:
- Only extracts text (no OCR for image-based PDFs)
- Tables and complex layouts may have formatting issues
- Images and charts are ignored

**Chunking Strategy Improvement Ideas**:
- Add 100-character overlap between chunks for better coherence
- Implement recursive summarization for very long documents (summarize summaries)
- Parallelize HF API calls with rate limiting (requires Pro tier)

## Troubleshooting Common Issues

**"HF_API_TOKEN environment variable not set"**:
- Local: `export HF_API_TOKEN=...` before running uvicorn
- Vercel: Use `vercel env add HF_API_TOKEN`

**"Processing timeout"**:
- PDF likely >10 pages or very dense
- Reduce max_chunk_size in [api/utils/summarizer.py](api/utils/summarizer.py)
- Or implement chunked response streaming

**"No text found in PDF"**:
- PDF may be image-based (scanned document)
- Suggest using OCR tool first (like Adobe Acrobat, Tesseract)

**Frontend not connecting to backend**:
- Check Vite proxy is configured ([vite.config.ts](vite.config.ts))
- Verify FastAPI is running on port 8000
- Clear browser cache and restart dev server

**Vercel deployment builds but functions fail**:
- Check logs: `vercel logs <deployment-url>`
- Verify Python version compatibility (3.9-3.11 supported)
- Ensure all imports are in requirements.txt
- Check function memory/timeout settings in vercel.json

## Performance Optimization Opportunities

1. **Caching**: Add Redis/KV for frequently summarized documents
2. **Progress tracking**: WebSocket/SSE for real-time progress on long PDFs
3. **Parallel processing**: Multiple HF API calls simultaneously (with rate limiting)
4. **Client-side chunking**: Upload PDF, extract text client-side, send only text to API
5. **Model quantization**: If moving back to local model, use quantized version (~400MB)

## Security Considerations

- File validation prevents non-PDF uploads
- Size limit prevents DoS via large files
- In-memory processing prevents disk-based attacks
- CORS should be restricted to production domains
- HF_API_TOKEN kept in environment, never in code
- Consider adding rate limiting per IP
