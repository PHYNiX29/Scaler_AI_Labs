"use client";

import { useEffect, useRef, useState } from "react";
import { Clock } from "lucide-react";
import { AnswerValue, Form, Question, ThemeSettings } from "@/types";
import { mediaSrc } from "@/lib/api";
import AnswerInput from "./AnswerInput";

/** The form's theme as CSS variables; everything on the canvas (.tf-* classes) reads these. */
export const themeVars = (theme: ThemeSettings) =>
  ({
    "--tf-bg": theme.background_color,
    "--tf-text": theme.text_color,
    "--tf-btn": theme.button_color,
    "--tf-btn-text": theme.button_text_color,
    backgroundColor: theme.background_color, // not the `background` shorthand: it would clash with the wallpaper's backgroundImage
    color: theme.text_color,
    fontFamily: `${theme.font_family}, var(--font-sans)`,
  }) as React.CSSProperties;

/** True when the element is phone-width. Measured (not a media query) so the builder's mobile preview frame counts too. */
function useIsNarrow(ref: React.RefObject<HTMLElement | null>) {
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const observer = new ResizeObserver(([entry]) => setNarrow(entry.contentRect.width < 720));
    observer.observe(ref.current!);
    return () => observer.disconnect();
  }, [ref]);
  return narrow;
}

interface Props {
  form: Form;
  question: Question;
  /** 1-based position among the real questions; screens have none */
  number?: number;
  value?: AnswerValue;
  error?: string | null;
  onChange?: (value: AnswerValue) => void;
  /** Advance to the next page, optionally with a value that was just picked */
  onSubmit?: (value?: AnswerValue) => void;
  /** Builder mode: title and description become inline-editable and the answer widget is inert */
  onEdit?: (patch: Partial<Question>) => void;
}

/**
 * One full page of a form, laid out the Typeform way. The respondent flow and the builder canvas
 * both render this, so what the creator edits is exactly what the respondent sees.
 */
export default function QuestionView({ form, question, number, value, error, onChange, onSubmit, onEdit }: Props) {
  const root = useRef<HTMLDivElement>(null);
  const narrow = useIsNarrow(root);
  const { media, properties: props, question_type: type } = question;
  const isWelcome = type === "welcome";
  const isEnding = type === "thank_you";

  // Which of the six layouts applies: phones only support image-on-top or wallpaper
  const src = media?.media_url ? mediaSrc(media.media_url) : null;
  const layout = !src
    ? "none"
    : narrow
      ? media.mobile_orientation === "wallpaper" ? "wallpaper" : "stack"
      : media.desktop_orientation;
  const isSplit = layout.startsWith("split");
  const isSide = isSplit || layout.startsWith("float");
  const centered = (isWelcome || isEnding) && !isSide;

  const mediaElement = (className: string) =>
    media.media_type === "video" ? (
      <video src={src!} className={className} autoPlay muted loop playsInline />
    ) : (
      // eslint-disable-next-line @next/next/no-img-element -- creator-supplied URLs from any host
      <img src={src!} alt={media.alt_text || ""} className={className} />
    );

  const titleClass = `w-full bg-transparent outline-none ${isWelcome || isEnding ? "text-4xl leading-tight" : "text-2xl"} ${centered ? "text-center" : ""}`;
  const descriptionClass = `mt-2 w-full bg-transparent text-xl opacity-70 outline-none ${centered ? "text-center" : ""}`;

  return (
    <div
      ref={root}
      className="flex h-full w-full bg-cover bg-center"
      style={{ ...themeVars(form.theme_settings), backgroundImage: layout === "wallpaper" ? `url("${src}")` : undefined }}
    >
      {isSide && (
        <div
          className={`h-full w-1/2 shrink-0 ${layout.endsWith("left") ? "order-first" : "order-last"} ${
            isSplit ? "" : "flex items-center justify-center p-[5%]"
          }`}
        >
          {mediaElement(isSplit ? "h-full w-full object-cover" : "max-h-[75%] w-full object-cover")}
        </div>
      )}

      <div className="flex h-full min-w-0 flex-1 overflow-y-auto px-6 sm:px-12">
        {/* m-auto centres the page vertically but still lets tall pages scroll from the top */}
        <div className="m-auto flex w-full max-w-[720px] items-start gap-3 py-20">
          {number !== undefined && (
            <span className="mt-1.5 grid h-5 min-w-5 place-items-center rounded px-1 text-xs font-bold" style={{ background: "var(--tf-text)", color: "var(--tf-bg)" }}>
              {number}
            </span>
          )}

          <div className={`min-w-0 flex-1 ${centered ? "flex flex-col items-center text-center" : ""}`}>
            {onEdit ? (
              <>
                <input
                  className={titleClass}
                  value={question.title}
                  placeholder="Your question here."
                  aria-label="Question title"
                  onChange={(e) => onEdit({ title: e.target.value })}
                />
                <input
                  className={`${descriptionClass} italic`}
                  value={question.description ?? ""}
                  placeholder="Description (optional)"
                  aria-label="Question description"
                  onChange={(e) => onEdit({ description: e.target.value })}
                />
              </>
            ) : (
              <>
                <h1 className={titleClass}>
                  {question.title}
                  {question.required && <span aria-label="required"> *</span>}
                </h1>
                {question.description && <p className={descriptionClass}>{question.description}</p>}
              </>
            )}

            {layout === "stack" && mediaElement("mt-6 max-h-72 max-w-full rounded object-cover")}

            <div className="mt-8 w-full" inert={!!onEdit}>
              {isWelcome && (
                <>
                  <button type="button" className="tf-btn px-5 py-2.5 text-xl" onClick={() => onSubmit?.()}>
                    {props.button_text || "Start"}
                  </button>
                  {props.stat_badge_type === "time_to_complete" && (
                    <p className={`mt-3 flex items-center gap-1 text-sm ${centered ? "justify-center" : ""}`}>
                      <Clock className="h-3.5 w-3.5" /> Takes {props.estimated_time_minutes || 1} minute
                      {(props.estimated_time_minutes || 1) > 1 && "s"}
                    </p>
                  )}
                  {props.stat_badge_type === "submissions" && (
                    <p className="mt-3 text-sm">{form.submissions_count} people have filled this out</p>
                  )}
                </>
              )}

              {isEnding && props.button_text && (
                <a className="tf-btn inline-block px-5 py-2.5 text-xl" href={props.button_url || "/"} target="_blank" rel="noreferrer">
                  {props.button_text}
                </a>
              )}

              {!isWelcome && !isEnding && (
                <>
                  <AnswerInput question={question} value={value} onChange={onChange} onSubmit={onSubmit} />
                  {error && (
                    <p role="alert" className="mt-4 inline-block rounded bg-[#f7e6e6] px-3 py-1 text-sm text-[#af0404]">
                      {error}
                    </p>
                  )}
                  <div className="mt-6 flex items-center gap-3">
                    <button type="button" className="tf-btn" onClick={() => onSubmit?.()}>
                      OK
                    </button>
                    <span className="text-xs">
                      press <b>Enter ↵</b>
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
