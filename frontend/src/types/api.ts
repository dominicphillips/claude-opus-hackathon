export interface Character {
  id: string;
  name: string;
  show_name: string;
  personality: string;
  speech_pattern: string;
  themes: string;
  avatar_url: string | null;
  voice_config: Record<string, unknown>;
}

export interface Scenario {
  id: string;
  type: string;
  name: string;
  description: string;
  structure: string[];
  example_prompt: string | null;
  icon: string | null;
}

export interface Child {
  id: string;
  name: string;
  age: number | null;
  interests: string[] | null;
  favorite_show: string | null;
}

export interface Clip {
  id: string;
  child_id: string;
  character_id: string;
  scenario_type: string;
  parent_note: string | null;
  status: string;
  generated_script: string | null;
  scene_description: {
    setting?: string;
    mood?: string;
    ambient_sounds?: string[];
  } | null;
  safety_status: string | null;
  safety_feedback: string | null;
  safety_checks: Record<string, { pass: boolean; note: string }> | null;
  audio_url: string | null;
  duration_seconds: number | null;
  generation_time_ms: number | null;
  created_at: string;
}

export interface ImageAsset {
  filename: string;
  path: string;
  category: string;
  url: string;
  size_bytes: number;
  title?: string;
  source?: string;
  relevance?: string;
}
