"use client";

import { ArrowDownRight, Blocks, Mail, Plus, Settings, Split, Users, Workflow } from "lucide-react";
import { Question } from "@/types";
import { isScreen } from "@/lib/respondent";
import { canBranch, QuestionBadge } from "@/components/question/questionMeta";
import { useToast } from "@/components/ui/Toast";

interface Props {
  questions: Question[];
  onEditLogic: (question: Question) => void;
}

// Diagram geometry (px)
const NODE_W = 84;
const NODE_H = 48;
const STEP_X = 150;
const STEP_Y = 76;
const ROW_Y = 190;
const PAD = 40;

/**
 * The form drawn as a flow: pages left to right in order, endings stacked on the right.
 * Grey lines are the default order; purple arcs are branching rules, labelled with the answer that triggers them.
 */
export default function WorkflowCanvas({ questions, onEditLogic }: Props) {
  const toast = useToast();
  const soon = (what: string) => () => toast(`${what} is coming soon`);

  const row = questions.filter((q) => q.question_type !== "thank_you"); // welcome + real questions
  const endings = questions.filter((q) => q.question_type === "thank_you");
  const real = questions.filter((q) => !isScreen(q));

  // Top-left corner of every node
  const position = new Map<string, { x: number; y: number }>();
  row.forEach((q, i) => position.set(q.id, { x: PAD + i * STEP_X, y: ROW_Y }));
  endings.forEach((q, i) => position.set(q.id, { x: PAD + row.length * STEP_X, y: ROW_Y + i * STEP_Y }));

  const width = PAD * 2 + (row.length + 1) * STEP_X;
  const height = Math.max(420, ROW_Y + endings.length * STEP_Y + PAD);

  // Default order: each page to the next, the last one to the first ending
  const sequence = [...row, ...endings.slice(0, 1)];
  const defaultEdges = sequence.slice(1).map((to, i) => {
    const a = position.get(sequence[i].id)!;
    const b = position.get(to.id)!;
    return `M ${a.x + NODE_W} ${a.y + NODE_H / 2} L ${b.x} ${b.y + NODE_H / 2}`;
  });

  const ruleEdges = real.flatMap((q) =>
    q.logic_jumps.flatMap((rule) => {
      const from = position.get(q.id)!;
      const to = position.get(rule.target_question_id);
      if (!to) return []; // target was deleted; the engine falls back to the default order too
      const label =
        q.question_type === "yes_no"
          ? rule.choice_id === "yes" ? "Yes" : "No"
          : q.properties.choices?.find((c) => c.id === rule.choice_id)?.label;
      if (!label) return [];

      const startX = from.x + NODE_W / 2;
      const endX = to.x + NODE_W / 2;
      const below = to.y > ROW_Y; // lower endings are reached from underneath, everything else arcs over the top
      const lift = 40 + 14 * Math.round((endX - startX) / STEP_X);
      const path = below
        ? `M ${startX} ${from.y + NODE_H} C ${startX} ${to.y + NODE_H / 2}, ${startX} ${to.y + NODE_H / 2}, ${to.x} ${to.y + NODE_H / 2}`
        : `M ${startX} ${from.y} C ${startX} ${from.y - lift}, ${endX} ${from.y - lift}, ${endX} ${to.y}`;
      const labelAt = below ? { x: startX + 8, y: to.y + NODE_H / 2 - 8 } : { x: (startX + endX) / 2, y: from.y - lift * 0.75 - 6 };
      return [{ key: q.id + rule.choice_id, path, label, labelAt, anchor: below ? ("start" as const) : ("middle" as const) }];
    })
  );

  return (
    <div className="flex min-h-0 flex-1 gap-4 p-4 pt-0">
      <div className="card flex min-w-0 flex-1 flex-col overflow-hidden">
        <div className="flex items-center gap-6 border-b border-white px-6 py-3.5 text-sm">
          <span className="font-medium">Logic</span>
          {["Scoring", "Tagging", "Outcome quiz"].map((feature) => (
            <button key={feature} type="button" className="text-muted hover:text-ink" onClick={soon(feature)}>
              {feature}
            </button>
          ))}
        </div>

        <div className="workflow-grid flex min-h-0 flex-1 items-start gap-6 overflow-auto p-6">
          <div className="mt-[130px] w-56 shrink-0 rounded-2xl border border-dashed border-line p-5">
            <ArrowDownRight className="h-5 w-5" />
            <h3 className="mt-3 font-medium">Pull data in</h3>
            <p className="mt-1 text-sm text-muted">Track sources, identify respondents, and personalize the form with URL parameters.</p>
            <button type="button" aria-label="Add data source" className="icon-btn mt-3 border border-line bg-white" onClick={soon("Pull data in")}>
              <Plus className="h-4 w-4" />
            </button>
          </div>

          <div className="relative shrink-0" style={{ width, height }}>
            <svg width={width} height={height} className="absolute inset-0" aria-hidden>
              <defs>
                <marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
                  <path d="M0 0 L8 4 L0 8 z" fill="#8b5cf6" />
                </marker>
              </defs>
              {defaultEdges.map((d) => <path key={d} d={d} stroke="#bdbdbd" strokeWidth="1.5" fill="none" />)}
              {ruleEdges.map((edge) => (
                <g key={edge.key}>
                  <path d={edge.path} stroke="#8b5cf6" strokeWidth="1.5" fill="none" markerEnd="url(#arrow)" />
                  <text x={edge.labelAt.x} y={edge.labelAt.y} textAnchor={edge.anchor} fontSize="11" fill="#6d28d9">
                    {edge.label.length > 18 ? edge.label.slice(0, 17) + "…" : edge.label}
                  </text>
                </g>
              ))}
            </svg>

            {[...row, ...endings].map((q) => {
              const { x, y } = position.get(q.id)!;
              const label = isScreen(q) ? (q.question_type === "thank_you" ? String.fromCharCode(65 + endings.indexOf(q)) : undefined) : real.indexOf(q) + 1;
              return (
                <div key={q.id} className="absolute" style={{ left: x, top: y, width: NODE_W }}>
                  <div className="grid place-items-center rounded-lg bg-white shadow-sm" style={{ height: NODE_H }} title={q.title}>
                    <QuestionBadge type={q.question_type} label={label} />
                  </div>
                  {canBranch(q) && (
                    <button
                      type="button"
                      aria-label={`Edit branching for question ${label}`}
                      title="Edit branching"
                      onClick={() => onEditLogic(q)}
                      className="absolute -right-3 top-3 grid h-6 w-6 place-items-center rounded-full bg-plum text-white hover:bg-plum-hover"
                    >
                      <Split className="h-3 w-3" />
                    </button>
                  )}
                  <p className="mt-1.5 truncate text-center text-xs text-muted">{q.title || "Untitled"}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <aside className="card w-[300px] shrink-0 overflow-y-auto p-5">
        <h2 className="pb-4 font-medium">Actions</h2>
        {[
          { icon: Blocks, title: "Connect", text: "Send responses to the tools you already use." },
          { icon: Workflow, title: "Automations", text: "Activate automations based on submissions to this form." },
          { icon: Users, title: "Contacts", text: "Map form responses to create or update your contacts." },
        ].map(({ icon: Icon, title, text }) => (
          <div key={title} className="mb-4 rounded-2xl border border-dashed border-line p-5">
            <Icon className="h-6 w-6" />
            <h3 className="mt-3 font-medium">{title}</h3>
            <p className="mt-1 text-sm text-muted">{text}</p>
            <button type="button" aria-label={`Set up ${title}`} className="icon-btn mt-3 border border-line bg-white" onClick={soon(title)}>
              {title === "Contacts" ? <Settings className="h-4 w-4" /> : title === "Automations" ? <Mail className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
            </button>
          </div>
        ))}
      </aside>
    </div>
  );
}
