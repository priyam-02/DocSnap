# API Documentation

Complete API reference for the PDF Document Summarizer backend.

## Base URL

**Development**: `http://localhost:8000`
**Production**: `https://your-deployment.vercel.app`

## Authentication

No authentication required for current version. Rate limiting enforced per IP address.

---

## Endpoints

### GET /api/health

Health check endpoint to verify the API is running.

**Request:**
```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "PDF Summarizer API"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

### POST /api/summarize

Summarize a PDF document (standard, blocking request).

**Request:**

Content-Type: `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File (PDF) | Yes | PDF file to summarize (max 10MB) |
| `length_option` | String | No | Summary length: `"Short"`, `"Medium"` (default), or `"Long"` |
| `tone_option` | String | No | Summary tone: `"Neutral"` (default), `"Professional"`, or `"Casual"` |

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/summarize \
  -F "file=@document.pdf" \
  -F "length_option=Medium" \
  -F "tone_option=Professional"
```

**Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('file', file); // File object from input
formData.append('length_option', 'Medium');
formData.append('tone_option', 'Professional');

const response = await fetch('/api/summarize', {
  method: 'POST',
  body: formData,
});

const result = await response.json();
```

**Response (Success - 200 OK):**
```json
{
  "summary": "This document discusses the implementation of artificial intelligence systems in healthcare settings. The study examines patient outcomes and operational efficiency.",
  "formatted_summary": "This document discusses the implementation of artificial intelligence systems in healthcare settings. The study examines patient outcomes and operational efficiency.\n\nKey findings include improved diagnostic accuracy and reduced processing times. The research involved 500 participants across multiple medical facilities.\n\nRecommendations emphasize the importance of staff training and integration with existing electronic health record systems.",
  "extracted_text_preview": "Introduction\n\nArtificial intelligence (AI) has emerged as a transformative technology in modern healthcare. This study examines the implementation of AI-powered diagnostic systems across multiple hospital settings...",
  "success": true,
  "metadata": {
    "original_word_count": 5243,
    "summary_word_count": 147,
    "compression_ratio": 0.028
  }
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `summary` | String | Raw summary text (single paragraph) |
| `formatted_summary` | String | Summary formatted into readable paragraphs |
| `extracted_text_preview` | String | First 500 characters of extracted PDF text |
| `success` | Boolean | Always `true` for successful requests |
| `metadata` | Object | Additional information about the summarization |
| `metadata.original_word_count` | Integer | Word count of original document |
| `metadata.summary_word_count` | Integer | Word count of generated summary |
| `metadata.compression_ratio` | Float | Ratio of summary length to original (0-1) |

**Error Responses:**

#### 400 Bad Request - Invalid File Type
```json
{
  "detail": "Only PDF files are supported"
}
```

#### 400 Bad Request - File Too Large
```json
{
  "detail": "File too large (max 10MB)"
}
```

#### 400 Bad Request - No Text Found
```json
{
  "detail": "No text found in PDF. The file may contain only images."
}
```

#### 422 Unprocessable Entity - Invalid Options
```json
{
  "detail": [
    {
      "loc": ["body", "length_option"],
      "msg": "value is not a valid enumeration member; permitted: 'Short', 'Medium', 'Long'",
      "type": "type_error.enum"
    }
  ]
}
```

#### 429 Too Many Requests - Rate Limit Exceeded
```json
{
  "detail": "Too many requests. Please try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": "60 minutes"
}
```

**Response Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed per hour (e.g., "10")
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets
- `Retry-After`: Seconds until the rate limit resets (only on 429 errors)

#### 504 Gateway Timeout - Processing Timeout
```json
{
  "detail": "Processing timeout - document too large or processing took too long"
}
```

#### 500 Internal Server Error - Server Error
```json
{
  "detail": "Failed to process document: <error message>"
}
```

**Status Codes:**
- `200 OK` - Summary generated successfully
- `400 Bad Request` - Invalid file or parameters
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `504 Gateway Timeout` - Processing timeout (>50s)
- `500 Internal Server Error` - Server error

---

### POST /api/summarize-stream

Summarize a PDF document with real-time progress updates via Server-Sent Events (SSE).

**Request:**

Content-Type: `multipart/form-data` (same as `/api/summarize`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File (PDF) | Yes | PDF file to summarize (max 10MB) |
| `length_option` | String | No | Summary length: `"Short"`, `"Medium"` (default), or `"Long"` |
| `tone_option` | String | No | Summary tone: `"Neutral"` (default), `"Professional"`, or `"Casual"` |

**Example (cURL):**
```bash
curl -N -X POST http://localhost:8000/api/summarize-stream \
  -F "file=@document.pdf" \
  -F "length_option=Medium" \
  -F "tone_option=Neutral"
```

**Example (JavaScript - EventSource-like):**
```javascript
const formData = new FormData();
formData.append('file', file);
formData.append('length_option', 'Medium');
formData.append('tone_option', 'Neutral');

const response = await fetch('/api/summarize-stream', {
  method: 'POST',
  body: formData,
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('event:')) {
      const event = line.substring(6).trim();
      // Next line contains data
    } else if (line.startsWith('data:')) {
      const data = JSON.parse(line.substring(5).trim());
      handleEvent(event, data);
    }
  }
}
```

**Response (Server-Sent Events):**

Content-Type: `text/event-stream`

The endpoint streams events in the following order:

#### 1. extraction_started
Emitted when PDF text extraction begins.

```
event: extraction_started
data: {"message": "Extracting text from PDF..."}

```

#### 2. extraction_complete
Emitted when text extraction finishes.

```
event: extraction_complete
data: {
  "message": "Text extracted successfully",
  "word_count": 5243,
  "preview": "Introduction\n\nArtificial intelligence (AI) has emerged as a transformative technology..."
}

```

#### 3. chunk_processing (repeated)
Emitted when starting to process each chunk.

```
event: chunk_processing
data: {
  "message": "Processing chunk 1 of 6",
  "progress": 16.67
}

```

#### 4. chunk_complete (repeated)
Emitted when each chunk is summarized.

```
event: chunk_complete
data: {
  "message": "Chunk 1 summarized",
  "summary": "This document discusses the implementation of AI systems in healthcare.",
  "progress": 33.33
}

```

#### 5. formatting
Emitted when formatting the final summary.

```
event: formatting
data: {"message": "Formatting summary..."}

```

#### 6. complete
Emitted when the entire process is complete (final event).

```
event: complete
data: {
  "summary": "This document discusses the implementation of artificial intelligence systems...",
  "formatted_summary": "This document discusses the implementation...\n\nKey findings include...",
  "extracted_text_preview": "Introduction\n\nArtificial intelligence...",
  "metadata": {
    "original_word_count": 5243,
    "summary_word_count": 147,
    "compression_ratio": 0.028
  }
}

```

#### error (on failure)
Emitted if an error occurs at any stage.

```
event: error
data: {"message": "No text found in PDF. The file may contain only images."}

```

**Event Data Fields:**

| Event | Fields | Description |
|-------|--------|-------------|
| `extraction_started` | `message` | Status message |
| `extraction_complete` | `message`, `word_count`, `preview` | Extraction results |
| `chunk_processing` | `message`, `progress` | Chunk N of M, progress % |
| `chunk_complete` | `message`, `summary`, `progress` | Chunk summary, progress % |
| `formatting` | `message` | Formatting status |
| `complete` | `summary`, `formatted_summary`, `extracted_text_preview`, `metadata` | Final result |
| `error` | `message` | Error description |

**Progress Calculation:**

```
Stage weights:
- Extraction: 0-20%
- Summarization: 20-80% (divided by number of chunks)
- Formatting: 80-90%
- Complete: 100%

Example with 5 chunks:
- Extraction complete: 20%
- Chunk 1 complete: 20 + (60/5) = 32%
- Chunk 2 complete: 32 + (60/5) = 44%
- ...
- Chunk 5 complete: 80%
- Complete: 100%
```

**Error Responses:**

Same error responses as `/api/summarize` (400, 422, 429, 504, 500).

---

## Summary Options

### Length Options

| Option | Description | Token Range | Typical Output |
|--------|-------------|-------------|----------------|
| `Short` | Brief overview | 30-60 tokens | 1-2 sentences, key point only |
| `Medium` | Balanced summary | 50-120 tokens | 2-4 sentences, main points |
| `Long` | Detailed summary | 80-200 tokens | 4-6 sentences, comprehensive |

**Example outputs for the same document:**

**Short:**
> "This study examines AI implementation in healthcare, showing improved diagnostic accuracy and reduced processing times across 500 participants."

**Medium:**
> "This document discusses the implementation of artificial intelligence systems in healthcare settings, examining patient outcomes and operational efficiency. Key findings include improved diagnostic accuracy and reduced processing times. The research involved 500 participants across multiple medical facilities."

**Long:**
> "This comprehensive study examines the implementation of artificial intelligence systems in modern healthcare settings, with a focus on patient outcomes and operational efficiency improvements. The research demonstrates significant improvements in diagnostic accuracy rates and substantial reductions in processing times across all tested scenarios. The study involved 500 participants across multiple medical facilities over a 12-month period. Findings emphasize the critical importance of comprehensive staff training programs and seamless integration with existing electronic health record systems for successful implementation."

### Tone Options

| Option | Description | Style |
|--------|-------------|-------|
| `Neutral` | Objective, factual | Academic/technical style, no emotional language |
| `Professional` | Formal business tone | Corporate communication, actionable insights |
| `Casual` | Conversational, accessible | Easy to understand, friendly language |

**Example outputs for the same content:**

**Neutral:**
> "The study analyzed the implementation of AI diagnostic systems. Results indicated improved accuracy rates and reduced processing times."

**Professional:**
> "This comprehensive analysis demonstrates the strategic value of implementing AI-powered diagnostic systems, resulting in measurable improvements in accuracy and operational efficiency."

**Casual:**
> "This study looked at how AI is helping doctors diagnose patients better and faster. The results show it's making a real difference in healthcare."

---

## Rate Limiting

**Default Limits:**
- 10 requests per hour per IP address
- Configurable via `RATE_LIMIT_PER_HOUR` environment variable

**Rate Limit Headers:**

All responses include:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1642345678
```

**When Rate Limit Exceeded:**

Status: `429 Too Many Requests`

```json
{
  "detail": "Too many requests. Please try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": "60 minutes"
}
```

Headers:
```
Retry-After: 3600
X-RateLimit-Limit: 10
X-RateLimit-Reset: 1642345678
```

---

## File Requirements

### Supported Formats
- PDF only (`.pdf` extension)
- Text-based PDFs (not scanned images)

### Limitations
- Maximum file size: 10MB
- Maximum processing time: 50 seconds
- Must contain extractable text

### Best Practices

**Optimal Documents:**
- 5-10 pages
- Clean, selectable text
- Standard fonts
- No complex layouts

**May Cause Issues:**
- Scanned documents (no OCR support)
- Image-heavy PDFs
- Very large documents (>50 pages)
- Complex tables/charts
- Protected/encrypted PDFs

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "additional_field": "context-specific data"
}
```

### Common Error Codes

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `INVALID_FILE_TYPE` | 400 | File is not a PDF |
| `FILE_TOO_LARGE` | 400 | File exceeds 10MB |
| `NO_TEXT_FOUND` | 400 | PDF contains no extractable text |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `PROCESSING_TIMEOUT` | 504 | Processing took >50 seconds |
| `HF_API_ERROR` | 500 | HuggingFace API error |
| `EXTRACTION_ERROR` | 500 | PDF extraction failed |

### Retry Strategy

**For 429 (Rate Limit):**
- Wait for time specified in `Retry-After` header
- Implement exponential backoff for repeated failures

**For 500 (Server Error):**
- Retry up to 3 times with exponential backoff
- Wait 1s, 2s, 4s between attempts

**For 504 (Timeout):**
- Don't retry automatically
- Suggest user to try smaller PDF or contact support

**Example Retry Logic (JavaScript):**
```javascript
async function summarizeWithRetry(file, options, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch('/api/summarize', {
        method: 'POST',
        body: createFormData(file, options),
      });

      if (response.ok) {
        return await response.json();
      }

      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After');
        await sleep(parseInt(retryAfter) * 1000);
        continue;
      }

      if (response.status >= 500) {
        if (attempt < maxRetries - 1) {
          await sleep(Math.pow(2, attempt) * 1000); // Exponential backoff
          continue;
        }
      }

      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    } catch (error) {
      if (attempt === maxRetries - 1) throw error;
    }
  }
}
```

---

## OpenAPI / Swagger Documentation

FastAPI automatically generates interactive API documentation.

**Swagger UI**: `http://localhost:8000/docs`
**ReDoc**: `http://localhost:8000/redoc`

Features:
- Try out endpoints directly in browser
- See request/response schemas
- Download OpenAPI JSON specification

**Access OpenAPI Spec:**
```bash
curl http://localhost:8000/openapi.json
```

---

## API Versioning

Current version: **v1** (implicit, no version in URL)

**Future versions** (if needed):
- `/v2/api/summarize` - New version
- `/api/summarize` - Legacy (v1)

**Deprecation Policy:**
- 6-month notice before removal
- Migration guide provided
- Automatic redirects when possible

---

## Security Considerations

### CORS

**Development**: Allows `http://localhost:5173`, `http://localhost:3000`
**Production**: Allows your Vercel domain only

**Custom domains** must be added to `CORS_ORIGINS` environment variable.

### Input Sanitization

All inputs are validated:
- File type checking (magic numbers, not just extension)
- File size limits enforced at middleware level
- Pydantic validation for all form fields

### No Data Persistence

- PDFs are processed in-memory only
- No files written to disk
- No database storage
- Ephemeral processing (serverless)

---

## Performance Expectations

| Document Size | Extraction | Summarization | Total |
|---------------|------------|---------------|-------|
| 1-2 pages | ~0.5s | ~2s | ~2.5s |
| 5 pages | ~1s | ~4s | ~5s |
| 10 pages | ~2s | ~8s | ~10s |
| 20 pages | ~4s | ~16s | ~20s |
| 50+ pages | ~10s+ | ~40s+ | May timeout |

**Factors affecting performance:**
- PDF complexity (images, tables)
- Text density
- HuggingFace API latency
- Network conditions

---

## Quotas & Limits

### HuggingFace API

**Free Tier:**
- 30,000 input characters per month
- ~12 typical PDFs (2,500 chars each)

**Pro Tier ($9/month):**
- 10,000,000 input characters per month
- ~4,000 typical PDFs

### Vercel

**Hobby Plan:**
- 10 concurrent serverless executions
- 10-second timeout per request
- 1GB total function size

**Pro Plan:**
- 100 concurrent executions
- 60-second timeout per request
- 3008MB memory per function

---

## Client Libraries

### Official
None yet (contributions welcome!)

### Community Examples

**Python:**
```python
import requests

def summarize_pdf(file_path, length="Medium", tone="Neutral"):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'length_option': length, 'tone_option': tone}
        response = requests.post(
            'http://localhost:8000/api/summarize',
            files=files,
            data=data
        )
        return response.json()
```

**Node.js:**
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function summarizePdf(filePath, options = {}) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  form.append('length_option', options.length || 'Medium');
  form.append('tone_option', options.tone || 'Neutral');

  const response = await axios.post(
    'http://localhost:8000/api/summarize',
    form,
    { headers: form.getHeaders() }
  );

  return response.data;
}
```

---

## Support & Feedback

- **Bug Reports**: [GitHub Issues](https://github.com/yourusername/document-summarizer/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/document-summarizer/discussions)
- **Questions**: Open an issue with `question` label

---

## Changelog

### v1.0.0 (Current)
- Initial release
- `/api/health` endpoint
- `/api/summarize` endpoint
- `/api/summarize-stream` endpoint with SSE
- Rate limiting (10 req/hour)
- Three length options (Short, Medium, Long)
- Three tone options (Neutral, Professional, Casual)
