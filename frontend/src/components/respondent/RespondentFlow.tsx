"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Answers, AnswerValue, Form, NextStep, Question } from "@/types";
import { api } from "@/lib/api";
import { isScreen, nextStep, validateAnswer } from "@/lib/respondent";
import QuestionView, { themeVars } from "@/components/question/QuestionView";

const FADE_OUT_MS = 250; // keep in sync with .page-out in globals.css

// Shown when a form has no ending screen of its own
const DEFAULT_ENDING = {
  id: "default-ending",
  question_type: "thank_you",
  title: "Thank you! Your response has been recorded.",
  properties: {},
  media: {},
} as Question;

interface Props {
  form: Form;
  /** Builder preview: nothing is sent to the server and branching is evaluated locally */
  isPreview?: boolean;
}

/** The one-question-at-a-time experience: fade between pages, keyboard navigation, progress bar. */
export default function RespondentFlow({ form, isPreview = false }: Props) {
  const questions = useMemo(
    () => [...(form.questions ?? [])].sort((a, b) => a.order_index - b.order_index),
    [form.questions]
  );
  const realQuestions = useMemo(() => questions.filter((q) => !isScreen(q)), [questions]);
  const firstPage = questions.find((q) => q.question_type === "welcome") ?? realQuestions[0] ?? DEFAULT_ENDING;

  const [current, setCurrent] = useState<Question>(firstPage);
  const [history, setHistory] = useState<Question[]>([]); // pages actually visited, so "previous" retraces branches
  const [answers, setAnswers] = useState<Answers>({});
  const [error, setError] = useState<string | null>(null);
  const [leaving, setLeaving] = useState(false);
  const [finished, setFinished] = useState(false);

  const busy = useRef(false); // blocks double submits (Enter + click) and input during the fade
  const session = useRef<{ id?: string; startedAt: number }>(null);

  useEffect(() => {
    if (session.current) return; // React strict mode runs effects twice in development
    session.current = { startedAt: Date.now() };
    // Records an in-progress response so abandoned fills show up in the completion rate
    if (!isPreview) api.startSession(form.slug).then((res) => (session.current!.id = res.session_id), () => {});
  }, [form.slug, isPreview]);

  /** Fade the current page out, swap, and let the new page fade in. */
  const goTo = (page: Question) => {
    busy.current = true;
    setLeaving(true);
    setTimeout(() => {
      setCurrent(page);
      setError(null);
      setLeaving(false);
      busy.current = false;
    }, FADE_OUT_MS);
  };

  const advance = async (picked?: AnswerValue) => {
    if (busy.current || finished) return;
    const value = picked ?? answers[current.id];

    let step: NextStep;
    if (current.question_type === "welcome") {
      step = { next_question_id: realQuestions[0]?.id ?? null, is_end: realQuestions.length === 0 };
    } else {
      const problem = validateAnswer(current, value);
      if (problem) return setError(problem);

      busy.current = true;
      try {
        if (isPreview) {
          step = nextStep(current, value, questions);
        } else {
          // The server validates the answer again and decides where the branching leads
          const result = await api.validateStep(form.slug, current.id, value);
          if (!result.valid) return setError(result.error ?? "Please check your answer");
          step = result as NextStep;
        }
        if (step.is_end && !isPreview) {
          await api.submitResponse(form.slug, {
            session_id: session.current?.id,
            answers: { ...answers, [current.id]: value },
            time_taken_seconds: Math.round((Date.now() - (session.current?.startedAt ?? Date.now())) / 1000),
          });
        }
      } catch (e) {
        return setError(e instanceof Error ? e.message : "Something went wrong. Please try again.");
      } finally {
        busy.current = false;
      }
    }

    if (step.is_end) setFinished(true);
    setHistory([...history, current]);
    goTo(questions.find((q) => q.id === step.next_question_id) ?? DEFAULT_ENDING);
  };

  const goBack = () => {
    if (busy.current || finished || history.length === 0) return;
    setHistory(history.slice(0, -1));
    goTo(history[history.length - 1]);
  };

  // Enter advances; arrow keys navigate unless the respondent is typing
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (finished) return;
      const typing = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault(); // also stops Enter from "clicking" a focused button a second time
        advance();
      } else if (e.key === "ArrowDown" && !typing) {
        e.preventDefault();
        advance();
      } else if (e.key === "ArrowUp" && !typing) {
        e.preventDefault();
        goBack();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const answeredCount = history.filter((q) => !isScreen(q)).length;
  const progress = finished ? 100 : realQuestions.length ? (answeredCount / realQuestions.length) * 100 : 0;
  const number = realQuestions.indexOf(current) + 1;

  return (
    <div className="relative h-full w-full overflow-hidden" style={themeVars(form.theme_settings)}>
      <div
        className="absolute inset-x-0 top-0 z-10 h-1 bg-[color-mix(in_srgb,var(--tf-btn)_25%,transparent)]"
        role="progressbar"
        aria-label="Form progress"
        aria-valuenow={Math.round(progress)}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="h-full bg-[var(--tf-btn)] transition-[width] duration-500" style={{ width: `${progress}%` }} />
      </div>

      {/* key remounts the page on every change so the fade-in animation replays */}
      <div key={current.id} className={`h-full w-full ${leaving ? "page-out" : "page-in"}`}>
        <QuestionView
          form={form}
          question={current}
          number={number || undefined}
          value={answers[current.id]}
          error={error}
          onChange={(value) => {
            setAnswers({ ...answers, [current.id]: value });
            setError(null);
          }}
          onSubmit={advance}
        />
      </div>

      <div className="absolute bottom-4 right-4 z-10 flex items-center gap-2">
        {!finished && (
          <div className="flex overflow-hidden rounded-md">
            <button type="button" aria-label="Previous question" disabled={history.length === 0} onClick={goBack} className="tf-btn rounded-none p-1.5 disabled:opacity-50">
              <ChevronUp className="h-5 w-5" />
            </button>
            <span className="w-px bg-[var(--tf-btn-text)] opacity-30" />
            <button type="button" aria-label="Next question" onClick={() => advance()} className="tf-btn rounded-none p-1.5">
              <ChevronDown className="h-5 w-5" />
            </button>
          </div>
        )}
        <Link href="/" target="_blank" className="tf-btn px-3 py-2 text-xs font-normal">
          Powered by <b>Typeform clone</b>
        </Link>
      </div>
    </div>
  );
}
