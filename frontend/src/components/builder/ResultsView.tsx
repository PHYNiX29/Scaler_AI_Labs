"use client";

import { useCallback, useEffect, useState } from "react";
import { Download, Star, Trash2 } from "lucide-react";
import { AnswerValue, Form, FormResponse, FormStats, QuestionStat } from "@/types";
import { api } from "@/lib/api";
import { CONTACT_LABELS } from "@/lib/respondent";
import { QuestionBadge } from "@/components/question/questionMeta";
import Modal, { ConfirmModal } from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";

const formatDate = (iso?: string) =>
  iso ? new Date(iso + "Z").toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }) : "–"; // API times are UTC without a zone suffix

const formatDuration = (seconds = 0) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;

/** An answer as readable text: lists joined, contact objects as "Label: value" lines. */
function formatAnswer(value: AnswerValue): string {
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") {
    return Object.entries(value)
      .filter(([, v]) => v)
      .map(([field, v]) => `${CONTACT_LABELS[field as keyof typeof CONTACT_LABELS]?.[0] ?? field}: ${v}`)
      .join("\n");
  }
  return value === undefined || value === "" ? "–" : String(value);
}

function QuestionSummary({ stat, number }: { stat: QuestionStat; number: number }) {
  return (
    <section className="rounded-2xl bg-white p-6">
      <div className="flex items-start gap-3">
        <QuestionBadge type={stat.question_type} label={number} />
        <div>
          <h3 className="font-medium">{stat.title || "Untitled"}</h3>
          <p className="text-sm text-muted">
            {stat.total_answers} answer{stat.total_answers === 1 ? "" : "s"}
          </p>
        </div>
      </div>

      {stat.avg_rating !== undefined && (
        <p className="mt-4 flex items-center gap-2 text-2xl">
          <Star className="h-5 w-5 fill-current" /> {stat.avg_rating.toFixed(1)}
          <span className="text-sm text-muted">average out of {stat.max_rating}</span>
        </p>
      )}

      {stat.breakdown ? (
        <ul className="mt-4 flex flex-col gap-2.5">
          {stat.breakdown.map((row) => {
            const label = row.choice ?? `${row.rating} ★`;
            return (
              <li key={label} className="text-sm">
                <div className="mb-1 flex justify-between gap-4">
                  <span>{label}</span>
                  <span className="shrink-0 text-muted">
                    {row.count} · {Math.round(row.percentage)}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-panel">
                  <div className="h-full rounded-full bg-plum" style={{ width: `${row.percentage}%` }} />
                </div>
              </li>
            );
          })}
        </ul>
      ) : (
        <ul className="mt-4 flex flex-col gap-1.5 text-sm">
          {(stat.recent_entries ?? []).map((entry, i) => (
            <li key={i} className="whitespace-pre-line rounded-lg bg-panel px-3 py-2">
              {formatAnswer(entry as AnswerValue)}
            </li>
          ))}
          {!stat.recent_entries?.length && <li className="text-muted">No answers yet.</li>}
        </ul>
      )}
    </section>
  );
}

/** "Results" tab: headline numbers, per-question summaries, and the table of individual responses. */
export default function ResultsView({ form }: { form: Form }) {
  const toast = useToast();
  const [view, setView] = useState<"summary" | "responses">("summary");
  const [stats, setStats] = useState<FormStats | null>(null);
  const [responses, setResponses] = useState<FormResponse[]>([]);
  const [open, setOpen] = useState<FormResponse | null>(null);
  const [deleting, setDeleting] = useState<FormResponse | null>(null);

  const load = useCallback(() => {
    Promise.all([api.getStats(form.id), api.getResponses(form.id)]).then(
      ([s, r]) => {
        setStats(s.stats);
        setResponses(r.responses);
      },
      () => toast("Couldn't load results", "error")
    );
  }, [form.id, toast]);
  useEffect(load, [load]);

  const remove = async (response: FormResponse) => {
    try {
      await api.deleteResponse(form.id, response.id);
      toast("Response deleted");
      load();
    } catch {
      toast("Couldn't delete the response", "error");
    }
  };

  if (!stats) return <div className="card m-4 mt-0 grid flex-1 place-items-center text-sm text-muted">Loading results…</div>;

  const headline = [
    ["Views", stats.views_count],
    ["Starts", stats.total_responses],
    ["Submissions", stats.completed_count],
    ["Completion rate", `${stats.completion_rate}%`],
    ["Time to complete", formatDuration(stats.avg_time_seconds)],
  ];

  return (
    <div className="card m-4 mt-0 flex-1 overflow-y-auto p-6">
      <div className="mx-auto max-w-4xl">
        <div className="flex items-center justify-between">
          <div role="tablist" className="flex rounded-lg bg-white p-1 text-sm">
            {(["summary", "responses"] as const).map((v) => (
              <button key={v} type="button" role="tab" aria-selected={view === v} onClick={() => setView(v)} className={`rounded-md px-4 py-1.5 capitalize ${view === v ? "bg-plum text-white" : "text-muted"}`}>
                {v} {v === "responses" && `[${responses.length}]`}
              </button>
            ))}
          </div>
          <a href={api.exportCsvUrl(form.id)} className="btn-secondary">
            <Download className="h-4 w-4" /> Export CSV
          </a>
        </div>

        <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-5">
          {headline.map(([label, value]) => (
            <div key={label} className="rounded-2xl bg-white p-4">
              <dt className="text-sm text-muted">{label}</dt>
              <dd className="mt-1 text-2xl">{value}</dd>
            </div>
          ))}
        </dl>

        {view === "summary" ? (
          <div className="mt-5 flex flex-col gap-4">
            {stats.questions.map((stat, i) => <QuestionSummary key={stat.question_id} stat={stat} number={i + 1} />)}
            {stats.questions.length === 0 && <p className="text-sm text-muted">This form has no questions yet.</p>}
          </div>
        ) : responses.length === 0 ? (
          <p className="mt-10 text-center text-muted">No responses yet. Share your form to start collecting them.</p>
        ) : (
          <div className="mt-5 overflow-x-auto rounded-2xl bg-white">
            <table className="w-full text-left text-sm">
              <thead className="text-muted">
                <tr>
                  {["Started", "Status", "Time taken", "Answers", ""].map((h) => <th key={h} className="px-4 py-3 font-normal">{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {responses.map((r) => (
                  <tr key={r.id} className="border-t border-line hover:bg-panel">
                    <td className="px-4 py-3">
                      <button type="button" className="underline-offset-2 hover:underline" onClick={() => api.getResponse(form.id, r.id).then((res) => setOpen(res.response), () => toast("Couldn't load the response", "error"))}>
                        {formatDate(r.started_at)}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${r.status === "completed" ? "bg-[#d9f2e6] text-brand-green" : "bg-panel text-muted"}`}>
                        {r.status === "completed" ? "Completed" : "Partial"}
                      </span>
                    </td>
                    <td className="px-4 py-3">{r.status === "completed" ? formatDuration(r.time_taken_seconds) : "–"}</td>
                    <td className="px-4 py-3">{Object.keys(r.answers ?? {}).length}</td>
                    <td className="px-2 text-right">
                      <button type="button" aria-label="Delete response" className="icon-btn hover:text-[#c0392b]" onClick={() => setDeleting(r)}>
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {open && (
        <Modal title={`Response · ${formatDate(open.submitted_at ?? open.started_at)}`} onClose={() => setOpen(null)} wide>
          <dl className="flex max-h-[60vh] flex-col gap-4 overflow-y-auto">
            {open.answers_breakdown?.map((answer, i) => (
              <div key={answer.question_id}>
                <dt className="flex items-center gap-2 text-sm text-muted">
                  <QuestionBadge type={answer.question_type} label={i + 1} /> {answer.question_title}
                </dt>
                <dd className="mt-1 whitespace-pre-line pl-1">{formatAnswer(answer.value)}</dd>
              </div>
            ))}
            {!open.answers_breakdown?.length && <p className="text-sm text-muted">This respondent left before answering anything.</p>}
          </dl>
        </Modal>
      )}
      {deleting && (
        <ConfirmModal title="Delete this response?" message="The response and its answers will be permanently removed." confirmLabel="Delete" onConfirm={() => remove(deleting)} onClose={() => setDeleting(null)} />
      )}
    </div>
  );
}
