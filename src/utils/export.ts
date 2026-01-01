import type { SummarizeResponse } from '../types';

export function downloadAsText(result: SummarizeResponse, filename: string) {
  const content = formatSummaryForExport(result, 'text');
  downloadFile(content, `summary_${filename}.txt`, 'text/plain');
}

export function downloadAsMarkdown(result: SummarizeResponse, filename: string) {
  const content = formatSummaryForExport(result, 'markdown');
  downloadFile(content, `summary_${filename}.md`, 'text/markdown');
}

function formatSummaryForExport(result: SummarizeResponse, format: 'text' | 'markdown'): string {
  const date = new Date().toLocaleDateString();
  const metadata = result.metadata;

  if (format === 'markdown') {
    return `# Document Summary

**Generated**: ${date}
**Original Length**: ${metadata?.original_word_count || 'N/A'} words
**Summary Length**: ${metadata?.summary_word_count || 'N/A'} words
**Compression**: ${metadata?.compression_ratio ? (metadata.compression_ratio * 100).toFixed(1) + '%' : 'N/A'}

---

## Summary

${result.formatted_summary}

---

## Original Text Preview

${result.extracted_text_preview}
`;
  } else {
    return `DOCUMENT SUMMARY
=================

Generated: ${date}
Original Length: ${metadata?.original_word_count || 'N/A'} words
Summary Length: ${metadata?.summary_word_count || 'N/A'} words
Compression: ${metadata?.compression_ratio ? (metadata.compression_ratio * 100).toFixed(1) + '%' : 'N/A'}

-----------------
SUMMARY
-----------------

${result.formatted_summary}

-----------------
ORIGINAL TEXT PREVIEW
-----------------

${result.extracted_text_preview}
`;
  }
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
