"use client";

import { useState } from "react";
import { ArrowDown, ArrowRight, ArrowUp, ChevronDown, Lightbulb, Plus, Rows3, Trash2 } from "lucide-react";
import { Question } from "@/types";
import { isScreen } from "@/lib/respondent";
import { QuestionBadge } from "@/components/question/questionMeta";

interface Props {
  questions: Question[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onDelete: (question: Question) => void;
  /** New order of the real questions (screens keep their fixed places) */
  onReorder: (questionIds: string[]) => void;
  onAddEnding: () => void;
  onOpenWorkflow: () => void;
}

/** Left column of the builder: the ordered page list (drag to reorder) and the ending screens. */
export default function PagesSidebar({ questions, activeId, onSelect, onDelete, onReorder, onAddEnding, onOpenWorkflow }: Props) {
  const [dragId, setDragId] = useState<string | null>(null);
  const [overId, setOverId] = useState<string | null>(null);

  const welcome = questions.find((q) => q.question_type === "welcome");
  const real = questions.filter((q) => !isScreen(q));
  const endings = questions.filter((q) => q.question_type === "thank_you");

  /** Moves a question so it sits where `targetId` currently is. */
  const move = (id: string, targetId: string) => {
    const ids = real.map((q) => q.id);
    const from = ids.indexOf(id);
    const to = ids.indexOf(targetId);
    if (from === -1 || to === -1 || from === to) return;
    ids.splice(to, 0, ids.splice(from, 1)[0]);
    onReorder(ids);
  };

  const row = (q: Question, label: string | number | undefined, index?: number) => {
    const draggable = index !== undefined;
    return (
      <li
        key={q.id}
        draggable={draggable}
        onDragStart={(e) => {
          e.dataTransfer.effectAllowed = "move";
          e.dataTransfer.setData("text/plain", q.id); // Firefox only starts a drag when data is set
          setDragId(q.id);
        }}
        onDragOver={(e) => {
          if (!draggable || !dragId) return;
          e.preventDefault(); // marks this row as a valid drop target
          setOverId(q.id);
        }}
        onDrop={() => dragId && move(dragId, q.id)}
        onDragEnd={() => {
          setDragId(null);
          setOverId(null);
        }}
        className={`group relative rounded-xl border bg-white ${draggable ? "cursor-grab active:cursor-grabbing" : ""} ${
          q.id === activeId ? "border-transparent bg-[#e9e9e9]" : "border-line/70"
        } ${dragId === q.id ? "opacity-40" : ""} ${overId === q.id && dragId !== q.id ? "ring-2 ring-plum" : ""}`}
      >
        <button type="button" onClick={() => onSelect(q.id)} className="flex w-full items-center gap-2.5 p-3 text-left text-sm">
          <QuestionBadge type={q.question_type} label={label} />
          <span className="line-clamp-2 min-w-0 flex-1 break-words">{q.title || "…"}</span>
        </button>
        <div className="absolute right-1.5 top-1/2 hidden -translate-y-1/2 rounded-lg bg-white shadow group-focus-within:flex group-hover:flex">
          {draggable && (
            <>
              <button type="button" aria-label="Move up" disabled={index === 0} onClick={() => move(q.id, real[index - 1].id)} className="icon-btn h-7 w-7 disabled:opacity-30">
                <ArrowUp className="h-3.5 w-3.5" />
              </button>
              <button type="button" aria-label="Move down" disabled={index === real.length - 1} onClick={() => move(q.id, real[index + 1].id)} className="icon-btn h-7 w-7 disabled:opacity-30">
                <ArrowDown className="h-3.5 w-3.5" />
              </button>
            </>
          )}
          <button type="button" aria-label={`Delete ${q.title || "page"}`} onClick={() => onDelete(q)} className="icon-btn h-7 w-7 hover:text-[#c0392b]">
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </li>
    );
  };

  return (
    <aside className="flex h-full w-[280px] shrink-0 flex-col gap-4">
      <div className="card flex items-center gap-2.5 px-5 py-4 text-sm">
        <Rows3 className="h-4 w-4" /> Universal mode <ChevronDown className="ml-auto h-4 w-4" />
      </div>

      <div className="card flex min-h-0 flex-1 flex-col p-4">
        <h2 className="px-2 pb-3 font-medium">Pages</h2>
        <ul className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1">
          {welcome && row(welcome, undefined)}
          {real.map((q, i) => row(q, i + 1, i))}
          {real.length === 0 && <li className="px-2 py-4 text-sm text-muted">Use “Add content” to add your first question.</li>}
        </ul>
        <button type="button" onClick={onOpenWorkflow} className="mt-3 flex items-center gap-2 rounded-xl border border-dashed border-line p-3 text-left text-sm font-medium hover:bg-white">
          <Lightbulb className="h-4 w-4 shrink-0" />
          <span className="flex-1">Personalize with branching</span>
          <span className="icon-btn h-7 w-7 border border-line bg-white">
            <ArrowRight className="h-4 w-4" />
          </span>
        </button>
      </div>

      <div className="card max-h-[35%] overflow-y-auto p-4">
        <div className="flex items-center justify-between px-2 pb-3">
          <h2 className="font-medium">Endings</h2>
          <button type="button" aria-label="Add ending" onClick={onAddEnding} className="icon-btn border border-line bg-white">
            <Plus className="h-4 w-4" />
          </button>
        </div>
        <ul className="flex flex-col gap-2">{endings.map((q, i) => row(q, String.fromCharCode(65 + i)))}</ul>
      </div>
    </aside>
  );
}
