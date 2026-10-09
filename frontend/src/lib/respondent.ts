import { AnswerValue, CONTACT_FIELDS, NextStep, Question } from "@/types";

export const isScreen = (q: Question) => q.question_type === "welcome" || q.question_type === "thank_you";

export const EMAIL_RE = /^[\w.-]+@([\w-]+\.)+[\w-]{2,}$/;

export const CONTACT_LABELS: Record<(typeof CONTACT_FIELDS)[number], [label: string, placeholder: string]> = {
  first_name: ["First name", "Jane"],
  last_name: ["Last name", "Smith"],
  phone_number: ["Phone number", "(201) 555-0123"],
  email: ["Email", "name@example.com"],
  company: ["Company", "Acme Corporation"],
};

const isEmpty = (v: AnswerValue) =>
  v === undefined || v === "" || (typeof v === "object" && Object.values(v).every((x) => !x));

/**
 * Instant client-side check so the respondent gets feedback without a round trip.
 * The server runs the full rules again (validate-step and submit) and is the authority.
 */
export function validateAnswer(q: Question, value: AnswerValue): string | null {
  if (q.question_type === "contact") {
    const contact = (value ?? {}) as Record<string, string>;
    for (const field of CONTACT_FIELDS) {
      const cfg = q.properties.fields?.[field] ?? { enabled: true, required: false };
      if (!cfg.enabled) continue;
      const text = (contact[field] ?? "").trim();
      if (cfg.required && !text) return `${CONTACT_LABELS[field][0]} is required`;
      if (field === "email" && text && !EMAIL_RE.test(text)) return "Hmm... that email doesn't look right";
    }
  }
  if (isEmpty(value)) return q.required ? "Please fill this in" : null;
  if (q.question_type === "email" && !EMAIL_RE.test(String(value).trim())) return "Hmm... that email doesn't look right";
  if (q.question_type === "number") {
    const n = Number(value);
    if (Number.isNaN(n)) return "Numbers only please";
    if (q.properties.min != null && n < q.properties.min) return `Please enter a number of at least ${q.properties.min}`;
    if (q.properties.max != null && n > q.properties.max) return `Please enter a number of at most ${q.properties.max}`;
  }
  return null;
}

/**
 * Mirror of the backend logic engine (app/services/logic_engine.py), used only by the builder's
 * preview, where a draft form has no public endpoint to ask. Live forms always ask the server.
 */
export function nextStep(question: Question, answer: AnswerValue, questions: Question[]): NextStep {
  const choiceId =
    question.question_type === "yes_no"
      ? String(answer).toLowerCase() === "yes" ? "yes" : "no"
      : question.properties.choices?.find((c) => c.label === answer)?.id;

  const rule = question.logic_jumps?.find((r) => choiceId !== undefined && r.choice_id === choiceId);
  let target = questions.find((q) => q.id === rule?.target_question_id);
  if (!target) {
    const later = questions.slice(questions.indexOf(question) + 1).filter((q) => !isScreen(q));
    target = later[0] ?? questions.find((q) => q.question_type === "thank_you");
  }
  return { next_question_id: target?.id ?? null, is_end: !target || target.question_type === "thank_you" };
}
