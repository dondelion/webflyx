export interface Voice {
  id: string;
  name: string;
  description: string | null;
  status: "created" | "training" | "ready" | "failed";
  created_at: string;
  updated_at: string;
}

export interface AudioSample {
  id: string;
  voice_id: string;
  original_filename: string;
  duration_sec: number | null;
  sample_rate: number | null;
  channels: number | null;
  format: string | null;
  created_at: string;
}

export interface Chunk {
  id: string;
  sample_id: string;
  start_sec: number;
  end_sec: number;
  transcript: string | null;
  phonemes: string[] | null;
  selected: boolean;
  transcription_pending: boolean;
  created_at: string;
}

export interface TrainingJob {
  id: string;
  voice_id: string;
  mode: "zero_shot" | "finetune";
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  progress: number;
  celery_task_id: string | null;
  model_path: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface CategoryCoverage {
  covered: string[];
  missing: string[];
  score: number;
}

export interface ChunkSuggestion {
  chunk_id: string;
  sample_id: string;
  start_sec: number;
  end_sec: number;
  transcript: string | null;
  fills_phonemes: string[];
  gain: number;
}

export interface PhonemeGap {
  phoneme: string;
  example_word: string;
  category: string;
}

export interface CoverageReport {
  voice_id: string;
  score: number;
  covered_count: number;
  total_count: number;
  covered: string[];
  missing: PhonemeGap[];
  by_category: Record<string, CategoryCoverage>;
  suggestions: ChunkSuggestion[];
  suggested_sentences: string[];
}

export interface APIKey {
  id: string;
  name: string;
  voice_id: string | null;
  last_used_at: string | null;
  created_at: string;
}
