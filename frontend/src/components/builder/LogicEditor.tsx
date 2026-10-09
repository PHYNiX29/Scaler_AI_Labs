"use client";

import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { BranchRule, Question } from "@/types";
import { isScreen } from "@/lib/respondent";
import Modal from "@/components/ui/Modal";

interface Props {
  question: Question;
  questions: Question[];
  onSave: (rules: BranchRule[]) => void;
  onClose: () => void;
}

/** Branching for one question: for each possible answer, pick where the respondent goes next. */
export default function LogicEditor({ question, questions, onSave, onClose }: Props) {
  // choice id -> target question id. A choice with no entry follows the normal order.
  const [targets, setTargets] = useState<Record<string, string>>(
    Object.fromEntries(question.logic_jumps.map((rule) => [rule.choice_id, rule.target_question_id]))
  );

  const choices =
    question.question_type === "yes_no"
      ? [{ id: "yes", label: "Yes" }, { id: "no", label: "No" }]
      : question.properties.choices ?? [];

  // Only later questions and endings can be targets, so a rule can never send someone round in a loop
  const real = questions.filter((q) => !isScreen(q));
  const later = real.slice(real.indexOf(question) + 1);
  const endings = questions.filter((q) => q.question_type === "thank_you");

  const save = () => {
    const valid = new Set([...later, ...endings].map((q) => q.id));
    onSave(
      choices
        .filter((c) => valid.has(targets[c.id]))
        .map((c) => ({ choice_id: c.id, target_question_id: targets[c.id] }))
    );
    onClose();
  };

  return (
    <Modal title="Edit logic" onClose={onClose} wide>
      <p className="mb-4 text-sm text-muted">
        After <b className="text-ink">{question.title || "this question"}</b>, send people to a different page depending on
        their answer.
      </p>
      <div className="flex flex-col gap-3">
        {choices.map((choice) => (
          <div key={choice.id} className="flex flex-wrap items-center gap-3 rounded-xl bg-panel p-3 text-sm">
            <span className="text-muted">If answer is</span>
            <span className="rounded-md bg-[#e2d5f7] px-2 py-1 font-medium">{choice.label}</span>
            <ArrowRight className="h-4 w-4 text-muted" />
            <select
              aria-label={`Destination when the answer is ${choice.label}`}
              className="text-input min-w-0 flex-1"
              value={targets[choice.id] ?? ""}
              onChange={(e) => setTargets({ ...targets, [choice.id]: e.target.value })}
            >
              <option value="">Continue to the next question</option>
              {later.length > 0 && (
                <optgroup label="Jump to question">
                  {later.map((q) => (
                    <option key={q.id} value={q.id}>
                      {real.indexOf(q) + 1}. {q.title || "Untitled"}
                    </option>
                  ))}
                </optgroup>
              )}
              {endings.length > 0 && (
                <optgroup label="End the form with">
                  {endings.map((q, i) => (
                    <option key={q.id} value={q.id}>
                      Ending {String.fromCharCode(65 + i)}. {q.title || "Untitled"}
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </div>
        ))}
        <p className="px-3 text-sm text-muted">In all other cases, continue to the next question.</p>
      </div>
      <div className="mt-6 flex justify-end gap-2">
        <button type="button" className="btn-secondary" onClick={onClose}>
          Cancel
        </button>
        <button type="button" className="btn-primary" onClick={save}>
          Save
        </button>
      </div>
    </Modal>
  );
}
