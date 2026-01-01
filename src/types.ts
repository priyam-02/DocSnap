export type LengthOption = 'Short' | 'Medium' | 'Long';
export type ToneOption = 'Neutral' | 'Professional' | 'Casual';

export interface SummarizeResponse {
  summary: string;
  formatted_summary: string;
  extracted_text_preview: string;
  success: boolean;
  metadata?: {
    original_word_count: number;
    summary_word_count: number;
    compression_ratio: number;
  };
}

export interface AppState {
  file: File | null;
  lengthOption: LengthOption;
  toneOption: ToneOption;
  isLoading: boolean;
  result: SummarizeResponse | null;
  error: string | null;
}
