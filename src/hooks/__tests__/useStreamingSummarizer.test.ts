import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useStreamingSummarizer } from '../useStreamingSummarizer';

describe('useStreamingSummarizer', () => {
  beforeEach(() => {
    // Reset fetch mock
    global.fetch = vi.fn();
  });

  it('should initialize with idle state', () => {
    const { result } = renderHook(() => useStreamingSummarizer());

    expect(result.current.processingState.stage).toBe('idle');
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('should handle extraction_started event', async () => {
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    // Create a readable stream with SSE events
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: extraction_started\ndata: {"message":"Extracting..."}\n\n'));
        controller.close();
      },
    });

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        body: stream,
      } as Response)
    );

    const { result } = renderHook(() => useStreamingSummarizer());

    act(() => {
      result.current.summarizeStreaming(mockFile, 'Medium', 'Neutral');
    });

    await waitFor(() => {
      expect(result.current.processingState.stage).toBe('extracting');
    }, { timeout: 3000 });
  });

  it('should handle extraction_complete event', async () => {
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: extraction_started\ndata: {"message":"Starting"}\n\n'));
        controller.enqueue(encoder.encode('event: extraction_complete\ndata: {"message":"Done","word_count":100}\n\n'));
        controller.close();
      },
    });

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        body: stream,
      } as Response)
    );

    const { result } = renderHook(() => useStreamingSummarizer());

    act(() => {
      result.current.summarizeStreaming(mockFile, 'Medium', 'Neutral');
    });

    await waitFor(() => {
      expect(result.current.processingState.stage).toBe('summarizing');
    }, { timeout: 3000 });
  });

  it('should accumulate partial summaries from chunk_complete events', async () => {
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: extraction_started\ndata: {"message":"Starting"}\n\n'));
        controller.enqueue(encoder.encode('event: chunk_complete\ndata: {"message":"Chunk 1","summary":"First chunk","progress":50}\n\n'));
        controller.enqueue(encoder.encode('event: chunk_complete\ndata: {"message":"Chunk 2","summary":"Second chunk","progress":100}\n\n'));
        controller.close();
      },
    });

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        body: stream,
      } as Response)
    );

    const { result } = renderHook(() => useStreamingSummarizer());

    act(() => {
      result.current.summarizeStreaming(mockFile, 'Medium', 'Neutral');
    });

    await waitFor(() => {
      expect(result.current.processingState.partialSummary).toContain('First chunk');
      expect(result.current.processingState.partialSummary).toContain('Second chunk');
    }, { timeout: 3000 });
  });

  it('should handle complete event and set result', async () => {
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    const completeData = {
      summary: 'Final summary',
      formatted_summary: 'Formatted summary',
      extracted_text_preview: 'Preview',
      metadata: {
        original_word_count: 100,
        summary_word_count: 10,
        compression_ratio: 0.1,
      },
    };

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: extraction_started\ndata: {"message":"Starting"}\n\n'));
        controller.enqueue(encoder.encode(`event: complete\ndata: ${JSON.stringify(completeData)}\n\n`));
        controller.close();
      },
    });

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        body: stream,
      } as Response)
    );

    const { result } = renderHook(() => useStreamingSummarizer());

    act(() => {
      result.current.summarizeStreaming(mockFile, 'Medium', 'Neutral');
    });

    await waitFor(() => {
      expect(result.current.result).toBeTruthy();
      expect(result.current.result?.summary).toBe('Final summary');
      expect(result.current.processingState.stage).toBe('complete');
    }, { timeout: 3000 });
  });

  it('should handle error event', async () => {
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: error\ndata: {"message":"Something went wrong"}\n\n'));
        controller.close();
      },
    });

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        body: stream,
      } as Response)
    );

    const { result } = renderHook(() => useStreamingSummarizer());

    act(() => {
      result.current.summarizeStreaming(mockFile, 'Medium', 'Neutral');
    });

    await waitFor(() => {
      expect(result.current.error).toBe('Something went wrong');
      expect(result.current.processingState.stage).toBe('error');
    }, { timeout: 3000 });
  });

  it('should handle fetch failure', async () => {
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
      } as Response)
    );

    const { result } = renderHook(() => useStreamingSummarizer());

    act(() => {
      result.current.summarizeStreaming(mockFile, 'Medium', 'Neutral');
    });

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
      expect(result.current.processingState.stage).toBe('error');
    }, { timeout: 3000 });
  });

  it('should reset state when starting new summarization', async () => {
    const mockFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('event: extraction_started\ndata: {"message":"Starting"}\n\n'));
        controller.close();
      },
    });

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        body: stream,
      } as Response)
    );

    const { result } = renderHook(() => useStreamingSummarizer());

    // First summarization
    act(() => {
      result.current.summarizeStreaming(mockFile, 'Medium', 'Neutral');
    });

    await waitFor(() => {
      expect(result.current.processingState.stage).toBe('extracting');
    });

    // Second summarization should reset
    act(() => {
      result.current.summarizeStreaming(mockFile, 'Short', 'Professional');
    });

    expect(result.current.error).toBeNull();
    expect(result.current.result).toBeNull();
  });
});
