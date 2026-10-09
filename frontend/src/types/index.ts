export type QuestionType =
  | "welcome"
  | "short_text"
  | "long_text"
  | "multiple_choice"
  | "dropdown"
  | "email"
  | "number"
  | "yes_no"
  | "rating"
  | "contact"
  | "date"
  | "thank_you";

export type DesktopLayout = "stack" | "float_left" | "float_right" | "split_left" | "split_right" | "wallpaper";
export type MobileLayout = "stack" | "wallpaper";

export interface MediaConfig {
  media_type: "image" | "video" | null;
  media_url: string | null;
  desktop_orientation: DesktopLayout;
  mobile_orientation: MobileLayout;
  alt_text?: string;
}

export interface ChoiceOption {
  id: string;
  label: string;
}

/** "If the answer is this choice, go to that question (or ending)". choice_id is "yes"/"no" for yes_no questions. */
export interface BranchRule {
  choice_id: string;
  target_question_id: string;
}

export const CONTACT_FIELDS = ["first_name", "last_name", "phone_number", "email", "company"] as const;
export type ContactField = (typeof CONTACT_FIELDS)[number];

export interface ContactFieldConfig {
  enabled: boolean;
  required: boolean;
}

export interface QuestionProperties {
  // Welcome / ending screens
  button_text?: string;
  button_url?: string;
  stat_badge_type?: "time_to_complete" | "submissions" | "none";
  estimated_time_minutes?: number;
  // Choices
  choices?: ChoiceOption[];
  allow_multiple?: boolean;
  allow_other?: boolean;
  // Contact
  fields?: Partial<Record<ContactField, ContactFieldConfig>>;
  // Rating
  icon?: "star" | "heart" | "thumbs_up";
  max_rating?: number;
  // Text / number
  placeholder?: string;
  max_length?: number;
  min?: number;
  max?: number;
}

export interface Question {
  id: string;
  form_id: string;
  order_index: number;
  question_type: QuestionType;
  title: string;
  description?: string;
  required: boolean;
  properties: QuestionProperties;
  media: MediaConfig;
  logic_jumps: BranchRule[];
}

export interface ThemeSettings {
  font_family: string;
  text_color: string;
  background_color: string;
  button_color: string;
  button_text_color: string;
}

export interface Form {
  id: string;
  title: string;
  description?: string;
  slug: string;
  status: "draft" | "published";
  views_count: number;
  submissions_count: number;
  theme_settings: ThemeSettings;
  questions?: Question[];
  questions_count?: number;
  created_at?: string;
  updated_at?: string;
}

// An answer is a string, number, list of choice labels, or a contact object keyed by field
export type AnswerValue = string | number | string[] | Record<string, string> | undefined;
export type Answers = Record<string, AnswerValue>;

export interface AnswerItem {
  question_id: string;
  question_title: string;
  question_type: QuestionType;
  value: AnswerValue;
}

export interface FormResponse {
  id: string;
  form_id: string;
  status: "in_progress" | "completed";
  started_at?: string;
  submitted_at?: string;
  time_taken_seconds?: number;
  answers?: Answers;
  answers_breakdown?: AnswerItem[];
}

export interface QuestionStat {
  question_id: string;
  title: string;
  question_type: QuestionType;
  total_answers: number;
  breakdown?: Array<{ choice?: string; rating?: number; count: number; percentage: number }>;
  avg_rating?: number;
  max_rating?: number;
  recent_entries?: unknown[];
}

export interface FormStats {
  views_count: number;
  total_responses: number;
  completed_count: number;
  completion_rate: number;
  avg_time_seconds: number;
  questions: QuestionStat[];
}

export interface NextStep {
  next_question_id: string | null;
  is_end: boolean;
}
