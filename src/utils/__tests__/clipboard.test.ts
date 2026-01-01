import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { copyToClipboard } from '../clipboard';

describe('copyToClipboard', () => {
  let originalClipboard: Clipboard;

  beforeEach(() => {
    // Store original clipboard
    originalClipboard = navigator.clipboard;

    // Mock clipboard API using defineProperty to override readonly property
    Object.defineProperty(navigator, 'clipboard', {
      writable: true,
      configurable: true,
      value: {
        writeText: vi.fn(() => Promise.resolve()),
      },
    });
  });

  afterEach(() => {
    // Restore original clipboard
    Object.defineProperty(navigator, 'clipboard', {
      writable: true,
      configurable: true,
      value: originalClipboard,
    });
  });

  it('should copy text using Clipboard API', async () => {
    const text = 'Test summary';
    const result = await copyToClipboard(text);

    expect(result).toBe(true);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(text);
  });

  it('should handle clipboard API failure', async () => {
    Object.defineProperty(navigator, 'clipboard', {
      writable: true,
      configurable: true,
      value: {
        writeText: vi.fn(() => Promise.reject(new Error('Permission denied'))),
      },
    });

    const result = await copyToClipboard('Test');
    expect(result).toBe(false);
  });

  it('should use fallback when clipboard API is not available', async () => {
    // Add execCommand to document if it doesn't exist
    if (!document.execCommand) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (document as any).execCommand = vi.fn().mockReturnValue(true);
    }

    // Mock document.execCommand
    const execCommandSpy = vi.spyOn(document, 'execCommand').mockReturnValue(true);

    // Remove clipboard API
    Object.defineProperty(navigator, 'clipboard', {
      writable: true,
      configurable: true,
      value: undefined,
    });

    const result = await copyToClipboard('Test text');

    expect(result).toBe(true);
    expect(execCommandSpy).toHaveBeenCalledWith('copy');

    execCommandSpy.mockRestore();
  });

  it('should return false when fallback fails', async () => {
    // Add execCommand to document if it doesn't exist
    if (!document.execCommand) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (document as any).execCommand = vi.fn().mockReturnValue(false);
    }

    const execCommandSpy = vi.spyOn(document, 'execCommand').mockReturnValue(false);

    Object.defineProperty(navigator, 'clipboard', {
      writable: true,
      configurable: true,
      value: undefined,
    });

    const result = await copyToClipboard('Test');

    expect(result).toBe(false);

    execCommandSpy.mockRestore();
  });
});
