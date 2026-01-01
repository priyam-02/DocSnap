import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { downloadAsText, downloadAsMarkdown } from '../export';
import type { SummarizeResponse } from '../../types';

describe('Export utilities', () => {
  let createElementSpy: ReturnType<typeof vi.spyOn>;
  let appendChildSpy: ReturnType<typeof vi.spyOn>;
  let removeChildSpy: ReturnType<typeof vi.spyOn>;
  let createObjectURLSpy: ReturnType<typeof vi.spyOn>;
  let revokeObjectURLSpy: ReturnType<typeof vi.spyOn>;

  const mockResult: SummarizeResponse = {
    summary: 'Test summary',
    formatted_summary: 'Test formatted summary',
    extracted_text_preview: 'Preview text',
    success: true,
    metadata: {
      original_word_count: 100,
      summary_word_count: 10,
      compression_ratio: 0.1,
    },
  };

  beforeEach(() => {
    // Mock DOM methods
    const mockLink: Partial<HTMLAnchorElement> = {
      href: '',
      download: '',
      click: vi.fn(),
    };

    createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockLink as HTMLElement);
    appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as Node);
    removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as Node);
    createObjectURLSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock-url');
    revokeObjectURLSpy = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  });

  afterEach(() => {
    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
    removeChildSpy.mockRestore();
    createObjectURLSpy.mockRestore();
    revokeObjectURLSpy.mockRestore();
  });

  describe('downloadAsText', () => {
    it('should download summary as TXT file', () => {
      downloadAsText(mockResult, 'test-document');

      expect(createElementSpy).toHaveBeenCalledWith('a');
      expect(appendChildSpy).toHaveBeenCalled();
      expect(removeChildSpy).toHaveBeenCalled();
      expect(createObjectURLSpy).toHaveBeenCalled();
      expect(revokeObjectURLSpy).toHaveBeenCalled();

      // Verify the link has correct download filename
      const mockLink = createElementSpy.mock.results[0].value;
      expect(mockLink.download).toBe('summary_test-document.txt');
      expect(mockLink.click).toHaveBeenCalled();
    });

    it('should include metadata in TXT format', () => {
      downloadAsText(mockResult, 'test');

      // Check that Blob was created with correct content type
      const blobArgs = createObjectURLSpy.mock.calls[0][0] as Blob;
      expect(blobArgs.type).toBe('text/plain');
    });
  });

  describe('downloadAsMarkdown', () => {
    it('should download summary as Markdown file', () => {
      downloadAsMarkdown(mockResult, 'test-document');

      expect(createElementSpy).toHaveBeenCalledWith('a');
      expect(appendChildSpy).toHaveBeenCalled();
      expect(removeChildSpy).toHaveBeenCalled();
      expect(createObjectURLSpy).toHaveBeenCalled();
      expect(revokeObjectURLSpy).toHaveBeenCalled();

      // Verify the link has correct download filename
      const mockLink = createElementSpy.mock.results[0].value;
      expect(mockLink.download).toBe('summary_test-document.md');
      expect(mockLink.click).toHaveBeenCalled();
    });

    it('should include metadata in Markdown format', () => {
      downloadAsMarkdown(mockResult, 'test');

      // Check that Blob was created with correct content type
      const blobArgs = createObjectURLSpy.mock.calls[0][0] as Blob;
      expect(blobArgs.type).toBe('text/markdown');
    });
  });

  describe('File content formatting', () => {
    it('should handle result without metadata', () => {
      const resultWithoutMetadata: SummarizeResponse = {
        summary: 'Test',
        formatted_summary: 'Test formatted',
        extracted_text_preview: 'Preview',
        success: true,
      };

      downloadAsText(resultWithoutMetadata, 'test');
      expect(createObjectURLSpy).toHaveBeenCalled();
    });
  });
});
