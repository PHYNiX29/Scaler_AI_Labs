"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Monitor, Palette, Play, Plus, Settings, Smartphone } from "lucide-react";
import { Form, Question, QuestionType, ThemeSettings } from "@/types";
import { api } from "@/lib/api";
import { isScreen } from "@/lib/respondent";
import { ADDABLE_TYPES, newQuestion, QuestionBadge, QUESTION_META } from "@/components/question/questionMeta";
import QuestionView from "@/components/question/QuestionView";
import BuilderHeader, { BUILDER_TABS, BuilderTab } from "@/components/builder/BuilderHeader";
import PagesSidebar from "@/components/builder/PagesSidebar";
import SettingsPanel from "@/components/builder/SettingsPanel";
import DesignPanel from "@/components/builder/DesignPanel";
import LogicEditor from "@/components/builder/LogicEditor";
import WorkflowCanvas from "@/components/builder/WorkflowCanvas";
import ShareView from "@/components/builder/ShareView";
import ResultsView from "@/components/builder/ResultsView";
import PreviewModal from "@/components/preview/PreviewModal";
import Modal, { ConfirmModal } from "@/components/ui/Modal";
import { Menu, MenuItem } from "@/components/ui/controls";
import { useToast } from "@/components/ui/Toast";

const SAVE_DELAY_MS = 500;

/** Canonical page order: welcome screen, then the questions, then the endings. */
const arrange = (questions: Question[]) => [
  ...questions.filter((q) => q.question_type === "welcome"),
  ...questions.filter((q) => !isScreen(q)),
  ...questions.filter((q) => q.question_type === "thank_you"),
];

function Editor() {
  const { id: formId } = useParams<{ id: string }>();
  const toast = useToast();

  const [form, setForm] = useState<Form | null>(null);
  const [loadError, setLoadError] = useState(false);
  const requestedTab = useSearchParams().get("tab") as BuilderTab; // e.g. the dashboard's "Results" shortcut
  const [tab, setTab] = useState<BuilderTab>(BUILDER_TABS.includes(requestedTab) ? requestedTab : "content");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [designOpen, setDesignOpen] = useState(false);
  const [mobileCanvas, setMobileCanvas] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [logicFor, setLogicFor] = useState<Question | null>(null);
  const [deleting, setDeleting] = useState<Question | null>(null);

  useEffect(() => {
    api.getForm(formId).then(
      ({ form }) => {
        setForm({ ...form, questions: arrange(form.questions ?? []) });
        setActiveId(form.questions?.[0]?.id ?? null);
      },
      () => setLoadError(true)
    );
  }, [formId]);

  // Edits update the screen immediately and are saved shortly after the creator stops typing.
  // One pending save per key (a question id, "title", "theme"), so a burst of keystrokes is one request.
  const pendingSaves = useRef(new Map<string, { timer: ReturnType<typeof setTimeout>; run: () => void }>());
  const saveLater = (key: string, save: () => Promise<unknown>) => {
    clearTimeout(pendingSaves.current.get(key)?.timer);
    const run = () => {
      pendingSaves.current.delete(key);
      save().catch(() => toast("Couldn't save your changes", "error"));
    };
    pendingSaves.current.set(key, { timer: setTimeout(run, SAVE_DELAY_MS), run });
  };
  // Leaving the builder flushes whatever is still waiting
  useEffect(() => {
    const pending = pendingSaves.current;
    return () => pending.forEach(({ timer, run }) => (clearTimeout(timer), run()));
  }, []);

  if (loadError) {
    return (
      <div className="grid h-dvh place-items-center text-center">
        <div>
          <p className="text-muted">This form could not be found.</p>
          <Link href="/dashboard" className="btn-primary mt-4">Back to forms</Link>
        </div>
      </div>
    );
  }
  if (!form) return <Loading />;

  const questions = form.questions ?? [];
  const real = questions.filter((q) => !isScreen(q));
  const active = questions.find((q) => q.id === activeId) ?? questions[0];
  const logicQuestion = questions.find((q) => q.id === logicFor?.id); // always the latest copy, not the one captured on click
  const setQuestions = (next: Question[]) => setForm({ ...form, questions: next });

  const persistOrder = (ordered: Question[]) =>
    api.reorderQuestions(form.id, ordered.map((q) => q.id)).catch(() => toast("Couldn't save the new order", "error"));

  const addQuestion = async (type: QuestionType) => {
    try {
      const { question } = await api.addQuestion(form.id, newQuestion(type));
      const ordered = arrange([...questions, question]);
      setQuestions(ordered);
      setActiveId(question.id);
      setDesignOpen(false);
      persistOrder(ordered); // new rows are appended server-side, after the endings
    } catch {
      toast("Couldn't add the question", "error");
    }
  };

  const updateQuestion = (updated: Question) => {
    setQuestions(questions.map((q) => (q.id === updated.id ? updated : q)));
    saveLater(updated.id, () => api.updateQuestion(form.id, updated));
  };

  const deleteQuestion = async (question: Question) => {
    clearTimeout(pendingSaves.current.get(question.id)?.timer);
    pendingSaves.current.delete(question.id);
    try {
      await api.deleteQuestion(form.id, question.id);
      setQuestions(questions.filter((q) => q.id !== question.id));
      toast("Page deleted");
    } catch {
      toast("Couldn't delete the page", "error");
    }
  };

  const reorder = (realIds: string[]) => {
    const ordered = arrange([...questions.filter(isScreen), ...realIds.map((id) => real.find((q) => q.id === id)!)]);
    setQuestions(ordered);
    persistOrder(ordered);
  };

  const rename = (title: string) => {
    setForm({ ...form, title });
    if (title.trim()) saveLater("title", () => api.updateForm(form.id, { title: title.trim() }));
  };

  const setTheme = (theme_settings: ThemeSettings) => {
    setForm({ ...form, theme_settings });
    saveLater("theme", () => api.updateForm(form.id, { theme_settings }));
  };

  const setPublished = async (published: boolean) => {
    try {
      const { status } = await api.setPublished(form.id, published);
      setForm({ ...form, status });
      toast(published ? "Form published. It's live at its public link." : "Form unpublished");
    } catch {
      toast("Couldn't change the publish status", "error");
    }
  };

  return (
    <div className="flex h-dvh min-w-[1100px] flex-col">
      <BuilderHeader form={form} tab={tab} onTabChange={setTab} onRename={rename} onSetPublished={setPublished} />

      {tab === "content" && (
        <div className="flex min-h-0 flex-1 gap-4 p-4 pt-0">
          <PagesSidebar
            questions={questions}
            activeId={active?.id ?? null}
            onSelect={(id) => (setActiveId(id), setDesignOpen(false))}
            onDelete={setDeleting}
            onReorder={reorder}
            onAddEnding={() => addQuestion("thank_you")}
            onOpenWorkflow={() => setTab("workflow")}
          />

          <main className="flex min-w-0 flex-1 flex-col gap-4">
            <div className="card flex items-center gap-1 p-2.5">
              <Menu label="Add content" className="btn-primary" button={<><Plus className="h-4 w-4" /> Add content</>}>
                {!questions.some((q) => q.question_type === "welcome") && (
                  <MenuItem onClick={() => addQuestion("welcome")}>
                    <QuestionBadge type="welcome" /> Welcome Screen
                  </MenuItem>
                )}
                {ADDABLE_TYPES.map((type) => (
                  <MenuItem key={type} onClick={() => addQuestion(type)}>
                    <QuestionBadge type={type} /> {QUESTION_META[type].label}
                  </MenuItem>
                ))}
                <MenuItem onClick={() => addQuestion("thank_you")}>
                  <QuestionBadge type="thank_you" /> End Screen
                </MenuItem>
              </Menu>
              <span className="mx-2 h-5 w-px bg-line" />
              <button type="button" aria-pressed={designOpen} onClick={() => setDesignOpen(!designOpen)} className="flex h-8 items-center gap-2 rounded-lg px-2.5 text-sm hover:bg-[#ebebeb]">
                <Palette className="h-4 w-4" /> Design
              </button>
              <span className="mx-2 h-5 w-px bg-line" />
              <button type="button" aria-label={mobileCanvas ? "Show desktop layout" : "Show mobile layout"} onClick={() => setMobileCanvas(!mobileCanvas)} className="icon-btn">
                {mobileCanvas ? <Monitor className="h-4 w-4" /> : <Smartphone className="h-4 w-4" />}
              </button>
              <button type="button" aria-label="Preview form" title="Preview" onClick={() => setPreviewOpen(true)} className="icon-btn">
                <Play className="h-4 w-4" />
              </button>
              <button type="button" aria-label="Form settings" onClick={() => setSettingsOpen(true)} className="icon-btn">
                <Settings className="h-4 w-4" />
              </button>
            </div>

            {/* Live preview of the selected page: the same component respondents see, with editable text */}
            <div className="flex min-h-0 flex-1 justify-center">
              <div className={`h-full w-full overflow-hidden border border-line ${mobileCanvas ? "max-w-[390px] rounded-3xl" : ""}`}>
                {active ? (
                  <QuestionView
                    key={active.id}
                    form={form}
                    question={active}
                    number={real.indexOf(active) + 1 || undefined}
                    onEdit={(patch) => updateQuestion({ ...active, ...patch })}
                  />
                ) : (
                  <div className="grid h-full place-items-center text-sm text-muted">Use “Add content” to add your first question.</div>
                )}
              </div>
            </div>
          </main>

          {designOpen ? (
            <DesignPanel theme={form.theme_settings} onChange={setTheme} onClose={() => setDesignOpen(false)} />
          ) : (
            active && <SettingsPanel key={active.id} question={active} onChange={updateQuestion} onOpenLogic={() => setLogicFor(active)} />
          )}
        </div>
      )}

      {tab === "workflow" && <WorkflowCanvas questions={questions} onEditLogic={setLogicFor} />}
      {tab === "connect" && (
        <div className="card m-4 mt-0 grid flex-1 place-items-center text-center">
          <div>
            <h1 className="text-2xl">Integrations &amp; webhooks</h1>
            <p className="mt-2 text-muted">Coming soon: send responses to Sheets, Slack, or your own endpoint.</p>
          </div>
        </div>
      )}
      {tab === "share" && <ShareView form={form} onPublish={() => setPublished(true)} />}
      {tab === "results" && <ResultsView form={form} />}

      {previewOpen && <PreviewModal form={form} onClose={() => setPreviewOpen(false)} />}
      {logicQuestion && (
        <LogicEditor
          question={logicQuestion}
          questions={questions}
          onSave={(logic_jumps) => updateQuestion({ ...logicQuestion, logic_jumps })}
          onClose={() => setLogicFor(null)}
        />
      )}
      {deleting && (
        <ConfirmModal
          title="Delete this page?"
          message={`“${deleting.title || "Untitled"}” will be removed from the form. Answers already collected for it will be deleted too.`}
          confirmLabel="Delete"
          onConfirm={() => deleteQuestion(deleting)}
          onClose={() => setDeleting(null)}
        />
      )}
      {settingsOpen && (
        <Modal title="Settings" onClose={() => setSettingsOpen(false)}>
          <ul className="flex flex-col gap-2 text-sm">
            <li className="flex items-center justify-between rounded-xl bg-panel p-3">
              Theme
              <button type="button" className="btn-secondary" onClick={() => (setSettingsOpen(false), setDesignOpen(true))}>Open Design</button>
            </li>
            <li className="flex items-center justify-between rounded-xl bg-panel p-3">
              Thank-you screen
              <button type="button" className="btn-secondary" onClick={() => (setSettingsOpen(false), setDesignOpen(false), setActiveId(questions.find((q) => q.question_type === "thank_you")?.id ?? activeId))}>Edit ending</button>
            </li>
            {["Team collaboration & sharing", "Payments", "File upload questions", "Language & translations"].map((item) => (
              <li key={item} className="flex items-center justify-between rounded-xl bg-panel p-3 text-muted">
                {item} <span className="rounded-full bg-white px-2 py-0.5 text-xs">Coming soon</span>
              </li>
            ))}
          </ul>
        </Modal>
      )}
    </div>
  );
}

const Loading = () => <div className="grid h-dvh place-items-center text-sm text-muted">Loading…</div>;

// useParams needs a Suspense boundary so the static shell can prerender
export default function FormEditorPage() {
  return (
    <Suspense fallback={<Loading />}>
      <Editor />
    </Suspense>
  );
}
