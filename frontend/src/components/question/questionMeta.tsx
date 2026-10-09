import {
  AlignLeft,
  Calendar,
  ChevronDown,
  CircleSlash,
  Contact,
  Hash,
  ListChecks,
  LucideIcon,
  Mail,
  PanelLeft,
  PanelRight,
  Star,
  Type,
} from "lucide-react";
import { Question, QuestionType } from "@/types";

/** Label, icon and Typeform-style tint for each question type; drives the add menu, sidebar and workflow nodes. */
export const QUESTION_META: Record<QuestionType, { label: string; icon: LucideIcon; tint: string }> = {
  welcome: { label: "Welcome Screen", icon: PanelLeft, tint: "#e3e3e3" },
  short_text: { label: "Short Text", icon: Type, tint: "#bcdcf7" },
  long_text: { label: "Long Text", icon: AlignLeft, tint: "#bcdcf7" },
  multiple_choice: { label: "Multiple Choice", icon: ListChecks, tint: "#e2d5f7" },
  dropdown: { label: "Dropdown", icon: ChevronDown, tint: "#e2d5f7" },
  yes_no: { label: "Yes/No", icon: CircleSlash, tint: "#e2d5f7" },
  email: { label: "Email", icon: Mail, tint: "#f9c3d1" },
  number: { label: "Number", icon: Hash, tint: "#f7e2b5" },
  rating: { label: "Rating", icon: Star, tint: "#c3e7c0" },
  contact: { label: "Contact Info", icon: Contact, tint: "#e3e3e3" },
  date: { label: "Date", icon: Calendar, tint: "#f7e2b5" },
  thank_you: { label: "End Screen", icon: PanelRight, tint: "#e3e3e3" },
};

/** The question types offered in "Add content" (screens are added from their own buttons). */
export const ADDABLE_TYPES = (Object.keys(QUESTION_META) as QuestionType[]).filter(
  (t) => t !== "welcome" && t !== "thank_you"
);

/** Types whose answer is a single choice, so each choice can branch somewhere different. */
export const canBranch = (q: Question) =>
  q.question_type === "yes_no" ||
  q.question_type === "dropdown" ||
  (q.question_type === "multiple_choice" && !q.properties.allow_multiple);

/** The coloured icon chip with the question number (or ending letter) next to it. */
export function QuestionBadge({ type, label }: { type: QuestionType; label?: string | number }) {
  const { icon: Icon, tint } = QUESTION_META[type];
  return (
    <span className="flex h-6 shrink-0 items-center gap-2 rounded px-1.5 text-xs" style={{ background: tint }}>
      <Icon className="h-3.5 w-3.5" />
      {label !== undefined && <span className="min-w-3 text-center">{label}</span>}
    </span>
  );
}

/** Default properties for a freshly added question of each type. */
export function newQuestion(type: QuestionType): Partial<Question> {
  const choice = (label: string) => ({ id: crypto.randomUUID().slice(0, 8), label });
  const properties =
    type === "multiple_choice" || type === "dropdown"
      ? { choices: [choice("Choice 1"), choice("Choice 2")] }
      : type === "rating"
        ? { max_rating: 5, icon: "star" as const }
        : type === "welcome"
          ? { button_text: "Start", stat_badge_type: "time_to_complete" as const, estimated_time_minutes: 1 }
          : type === "thank_you"
            ? { button_text: "Create a typeform" }
            : {};
  const title = type === "welcome" ? "Welcome" : type === "thank_you" ? "Thank you for your time!" : "";
  return { question_type: type, title, properties };
}
