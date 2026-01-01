import { useState, useCallback } from 'react';
import type { SummarizeResponse } from '../types';

interface ProcessingState {
  stage: 'idle' | 'extracting' | 'summarizing' | 'formatting' | 'complete' | 'error';
  message: string;
  progress: number;
  currentChunk?: number;
  totalChunks?: number;
  partialSummary?: string;
}

export function useStreamingSummarizer() {
  const [processingState, setProcessingState] = useState<ProcessingState>({
    stage: 'idle',
    message: '',
    progress: 0,
  });
  const [result, setResult] = useState<SummarizeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const summarizeStreaming = useCallback(
    async (file: File, lengthOption: string, toneOption: string) => {
      setError(null);
      setResult(null);
      setProcessingState({
        stage: 'extracting',
        message: 'Starting...',
        progress: 0,
      });

      const formData = new FormData();
      formData.append('file', file);
      formData.append('length_option', lengthOption);
      formData.append('tone_option', toneOption);

      try {
        const response = await fetch('/api/summarize-stream', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Failed to start summarization');
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('Response body is not readable');
        }

        let buffer = '';
        const summaryParts: string[] = [];

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (line.startsWith('event:')) {
              const eventName = line.substring(6).trim();
              const nextLine = lines[i + 1];

              if (nextLine?.startsWith('data:')) {
                const data = JSON.parse(nextLine.substring(5).trim());

                switch (eventName) {
                  case 'extraction_started':
                    setProcessingState({
                      stage: 'extracting',
                      message: data.message,
                      progress: 10,
                    });
                    break;

                  case 'extraction_complete':
                    setProcessingState({
                      stage: 'summarizing',
                      message: `Extracted ${data.word_count} words`,
                      progress: 20,
                    });
                    break;

                  case 'chunk_processing':
                    setProcessingState(prev => ({
                      ...prev,
                      stage: 'summarizing',
                      message: data.message,
                      progress: 20 + data.progress * 0.6,
                    }));
                    break;

                  case 'chunk_complete':
                    summaryParts.push(data.summary);
                    setProcessingState(prev => ({
                      ...prev,
                      stage: 'summarizing',
                      message: data.message,
                      progress: 20 + data.progress * 0.6,
                      partialSummary: summaryParts.join(' '),
                    }));
                    break;

                  case 'formatting':
                    setProcessingState({
                      stage: 'formatting',
                      message: data.message,
                      progress: 90,
                    });
                    break;

                  case 'complete':
                    setResult(data);
                    setProcessingState({
                      stage: 'complete',
                      message: 'Summary complete!',
                      progress: 100,
                    });
                    break;

                  case 'error':
                    setError(data.message);
                    setProcessingState({
                      stage: 'error',
                      message: data.message,
                      progress: 0,
                    });
                    break;
                }
              }
            }
          }
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'An unexpected error occurred';
        setError(message);
        setProcessingState({
          stage: 'error',
          message,
          progress: 0,
        });
      }
    },
    []
  );

  return {
    processingState,
    result,
    error,
    summarizeStreaming,
  };
}
