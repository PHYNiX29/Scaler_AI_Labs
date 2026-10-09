"use client";

import { useEffect, useState } from "react";
import { Check, Heart, Search, Star, ThumbsUp } from "lucide-react";
import { AnswerValue, CONTACT_FIELDS, Question } from "@/types";
import { CONTACT_LABELS } from "@/lib/respondent";

interface Props {
  question: Question;
  value: AnswerValue;
  /** Omitted in the builder canvas, where the widgets are a non-interactive preview */
  onChange?: (value: AnswerValue) => void;
  /** Single-pick widgets call this with the picked value to move on without pressing OK */
  onSubmit?: (value: AnswerValue) => void;
}

const RATING_ICONS = { star: Star, heart: Heart, thumbs_up: ThumbsUp };
const OTHER = "Other: ";
const isTyping = (e: KeyboardEvent) => e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;

/** The answer widget for one question type. Values match what the backend validator expects. */
export default function AnswerInput({ question, value, onChange, onSubmit }: Props) {
  const { question_type: type, properties: props } = question;
  const [search, setSearch] = useState("");
  const [hovered, setHovered] = useState(0);
  const [picked, setPicked] = useState<AnswerValue>();

  // Blink the picked answer like Typeform does, then advance
  const pick = (v: AnswerValue) => {
    onChange?.(v);
    setPicked(v);
    setTimeout(() => onSubmit?.(v), 500);
  };

  const choices = type === "yes_no" ? [{ id: "yes", label: "Yes" }, { id: "no", label: "No" }] : props.choices ?? [];
  const multiple = type === "multiple_choice" && !!props.allow_multiple;
  const selected: string[] = Array.isArray(value) ? value : typeof value === "string" && value ? [value] : [];
  const maxRating = props.max_rating ?? 5;

  const toggle = (label: string) => {
    if (!multiple) return pick(label);
    onChange?.(selected.includes(label) ? selected.filter((s) => s !== label) : [...selected, label]);
  };

  // Keyboard shortcuts: A/B/C (or Y/N) pick a choice, 1-9 pick a rating
  useEffect(() => {
    if (!onChange) return;
    const onKey = (e: KeyboardEvent) => {
      if (isTyping(e) || e.ctrlKey || e.metaKey || e.altKey) return;
      const key = e.key.toUpperCase();
      if (type === "rating" && Number(key) >= 1 && Number(key) <= maxRating) pick(Number(key));
      if (type === "yes_no" && (key === "Y" || key === "N")) pick(key === "Y" ? "Yes" : "No");
      if (type === "multiple_choice" && key.length === 1) {
        const choice = choices[key.charCodeAt(0) - 65];
        if (choice) toggle(choice.label);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  if (type === "multiple_choice" || type === "yes_no") {
    const other = selected.find((s) => s.startsWith(OTHER));
    const setOther = (text: string) => {
      const entry = text ? [OTHER + text] : [];
      onChange?.(multiple ? [...selected.filter((s) => s !== other), ...entry] : entry[0]);
    };
    return (
      <div className="inline-flex min-w-[220px] max-w-full flex-col gap-2" role={multiple ? "group" : "radiogroup"}>
        {multiple && <p className="text-sm opacity-70">Choose as many as you like</p>}
        {choices.map((choice, i) => {
          const checked = selected.includes(choice.label);
          return (
            <button
              key={choice.id}
              type="button"
              role={multiple ? "checkbox" : "radio"}
              aria-checked={checked}
              onClick={() => toggle(choice.label)}
              className={`tf-choice ${picked === choice.label ? "choice-picked" : ""}`}
            >
              <span className="tf-key">{type === "yes_no" ? choice.label[0] : String.fromCharCode(65 + i)}</span>
              <span className="flex-1">{choice.label}</span>
              {checked && <Check className="h-4 w-4" />}
            </button>
          );
        })}
        {props.allow_other && (
          <input
            className="tf-choice"
            placeholder="Other"
            aria-label="Other answer"
            value={other?.slice(OTHER.length) ?? ""}
            onChange={(e) => setOther(e.target.value)}
          />
        )}
      </div>
    );
  }

  if (type === "dropdown") {
    const matches = choices.filter((c) => c.label.toLowerCase().includes(search.toLowerCase()));
    return (
      <div className="max-w-[520px] rounded-lg p-5 shadow-[0_0_0_2px_color-mix(in_srgb,var(--tf-text)_10%,transparent)]">
        <div className="relative">
          <input
            className="tf-input pr-8"
            placeholder="Type or select an option"
            aria-label="Search options"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Search className="absolute right-0 top-2 h-4 w-4" />
        </div>
        <div role="listbox" className="mt-5 flex max-h-56 flex-col gap-2 overflow-y-auto p-0.5">
          {matches.map((choice) => (
            <button
              key={choice.id}
              type="button"
              role="option"
              aria-selected={value === choice.label}
              onClick={() => pick(choice.label)}
              className={`tf-choice text-base ${picked === choice.label ? "choice-picked" : ""}`}
            >
              {choice.label}
            </button>
          ))}
          {matches.length === 0 && <p className="text-sm opacity-60">No suggestions found</p>}
        </div>
      </div>
    );
  }

  if (type === "rating") {
    const Icon = RATING_ICONS[props.icon ?? "star"];
    const lit = hovered || Number(value) || 0;
    return (
      <div className="flex flex-wrap gap-2" role="radiogroup" onMouseLeave={() => setHovered(0)}>
        {Array.from({ length: maxRating }, (_, i) => i + 1).map((n) => (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={value === n}
            aria-label={`${n} out of ${maxRating}`}
            onMouseEnter={() => onChange && setHovered(n)}
            onClick={() => pick(n)}
            className={`flex flex-col items-center gap-2 ${picked === n ? "choice-picked" : ""}`}
          >
            <Icon
              className="h-12 w-12"
              strokeWidth={1}
              fill={n <= lit ? "color-mix(in srgb, var(--tf-text) 85%, transparent)" : "transparent"}
            />
            <span className="text-sm">{n}</span>
          </button>
        ))}
      </div>
    );
  }

  if (type === "contact") {
    const contact = (value ?? {}) as Record<string, string>;
    return (
      <div className="flex max-w-[520px] flex-col gap-5">
        {CONTACT_FIELDS.filter((f) => props.fields?.[f]?.enabled ?? true).map((field) => (
          <label key={field} className="block text-base">
            {CONTACT_LABELS[field][0]}
            {props.fields?.[field]?.required && " *"}
            <input
              className="tf-input mt-1"
              type={field === "email" ? "email" : field === "phone_number" ? "tel" : "text"}
              autoComplete={{ first_name: "given-name", last_name: "family-name", phone_number: "tel", email: "email", company: "organization" }[field]}
              placeholder={CONTACT_LABELS[field][1]}
              value={contact[field] ?? ""}
              onChange={(e) => onChange?.({ ...contact, [field]: e.target.value })}
            />
          </label>
        ))}
      </div>
    );
  }

  const text = {
    value: (value as string | number | undefined) ?? "",
    "aria-label": question.title,
    autoFocus: !!onChange,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onChange?.(e.target.value),
  };

  if (type === "long_text") {
    return (
      <>
        <textarea
          {...text}
          className="tf-input"
          rows={Math.min(8, String(text.value).split("\n").length)}
          maxLength={props.max_length}
          placeholder={props.placeholder || "Type your answer here..."}
        />
        <p className="mt-2 text-xs opacity-70">
          <b>Shift ⇧ + Enter ↵</b> to make a line break
        </p>
      </>
    );
  }

  return (
    <input
      {...text}
      className="tf-input"
      type={type === "date" ? "date" : type === "email" ? "email" : "text"}
      inputMode={type === "number" ? "decimal" : undefined}
      maxLength={props.max_length}
      placeholder={props.placeholder || (type === "email" ? "name@example.com" : "Type your answer here...")}
    />
  );
}
