"use client";

import { useRef, useState } from "react";
import { Plus, Trash2, Upload, X } from "lucide-react";
import { CONTACT_FIELDS, DesktopLayout, MediaConfig, Question, QuestionProperties, QuestionType } from "@/types";
import { api, mediaSrc } from "@/lib/api";
import { CONTACT_LABELS, isScreen } from "@/lib/respondent";
import { ADDABLE_TYPES, canBranch, newQuestion, QUESTION_META } from "@/components/question/questionMeta";
import { Field, Toggle } from "@/components/ui/controls";
import { useToast } from "@/components/ui/Toast";

interface Props {
  question: Question;
  onChange: (question: Question) => void;
  onOpenLogic: () => void;
}

const DESKTOP_LAYOUTS: DesktopLayout[] = ["stack", "float_right", "float_left", "split_right", "split_left", "wallpaper"];

/** Miniature drawing of a layout: the dark block is the image, the lines are the question text. */
function LayoutIcon({ layout }: { layout: DesktopLayout }) {
  const image = {
    stack: { x: 6, y: 9, width: 16, height: 7 },
    float_right: { x: 16, y: 6, width: 8, height: 8 },
    float_left: { x: 4, y: 6, width: 8, height: 8 },
    split_right: { x: 15, y: 1, width: 12, height: 18 },
    split_left: { x: 1, y: 1, width: 12, height: 18 },
    wallpaper: { x: 1, y: 1, width: 26, height: 18 },
  }[layout];
  const textX = layout.endsWith("left") ? 15 : layout.endsWith("right") ? 4 : 9;
  const textY = layout === "stack" ? 5 : 9;
  const textColor = layout === "wallpaper" ? "#fff" : "currentColor";
  return (
    <svg viewBox="0 0 28 20" className="h-5 w-7" aria-hidden>
      <rect {...image} rx="2" fill="currentColor" opacity="0.75" />
      <rect x={textX} y={textY} width="8" height="1.5" rx="0.75" fill={textColor} />
      {layout !== "stack" && <rect x={textX} y={textY + 3} width="5" height="1.5" rx="0.75" fill={textColor} />}
    </svg>
  );
}

/** Right column of the builder: everything configurable about the selected page. */
export default function SettingsPanel({ question, onChange, onOpenLogic }: Props) {
  const toast = useToast();
  const fileInput = useRef<HTMLInputElement>(null);
  const [mediaOpen, setMediaOpen] = useState(false);
  const { question_type: type, properties: props, media } = question;

  const setProps = (patch: Partial<QuestionProperties>) => onChange({ ...question, properties: { ...props, ...patch } });
  const setMedia = (patch: Partial<MediaConfig>) => onChange({ ...question, media: { ...media, ...patch } });

  const changeType = (next: QuestionType) => {
    // Keep existing choices when switching between choice types; otherwise start from that type's defaults
    const defaults = newQuestion(next).properties!;
    onChange({ ...question, question_type: next, properties: { ...defaults, ...(props.choices && defaults.choices ? { choices: props.choices } : {}) }, logic_jumps: [] });
  };

  const upload = async (file: File) => {
    try {
      const { url, media_type } = await api.uploadMedia(file);
      setMedia({ media_url: url, media_type });
    } catch (e) {
      toast(e instanceof Error ? e.message : "Upload failed", "error");
    }
  };

  const choices = props.choices ?? [];
  const setChoice = (index: number, label: string) => setProps({ choices: choices.map((c, i) => (i === index ? { ...c, label } : c)) });

  return (
    <aside className="flex h-full w-[320px] shrink-0 flex-col gap-4 overflow-y-auto">
      <div className="card p-5">
        {isScreen(question) ? (
          <div className="text-input flex items-center gap-2">{QUESTION_META[type].label}</div>
        ) : (
          <select aria-label="Question type" className="text-input" value={type} onChange={(e) => changeType(e.target.value as QuestionType)}>
            {ADDABLE_TYPES.map((t) => (
              <option key={t} value={t}>
                {QUESTION_META[t].label}
              </option>
            ))}
          </select>
        )}

        <div className="mt-4 border-t border-line pt-3">
          {!isScreen(question) && <Toggle label="Required" checked={question.required} onChange={(required) => onChange({ ...question, required })} />}

          {type === "welcome" && (
            <>
              {/* The two badges are exclusive: the welcome screen shows one line under the button */}
              <Toggle label="Time to complete" checked={props.stat_badge_type === "time_to_complete"} onChange={(on) => setProps({ stat_badge_type: on ? "time_to_complete" : "none" })} />
              {props.stat_badge_type === "time_to_complete" && (
                <Field label="Minutes">
                  <input type="number" min={1} className="text-input" value={props.estimated_time_minutes ?? 1} onChange={(e) => setProps({ estimated_time_minutes: Math.max(1, Number(e.target.value)) })} />
                </Field>
              )}
              <Toggle label="Number of submissions" checked={props.stat_badge_type === "submissions"} onChange={(on) => setProps({ stat_badge_type: on ? "submissions" : "none" })} />
            </>
          )}

          {isScreen(question) && (
            <Field label="Button">
              <input className="text-input" maxLength={24} value={props.button_text ?? ""} onChange={(e) => setProps({ button_text: e.target.value })} />
              <span className="mt-1 block text-right text-xs text-muted">{(props.button_text ?? "").length}/24</span>
            </Field>
          )}
          {type === "thank_you" && (
            <Field label="Button link">
              <input className="text-input" type="url" placeholder="https://" value={props.button_url ?? ""} onChange={(e) => setProps({ button_url: e.target.value })} />
            </Field>
          )}

          {(type === "multiple_choice" || type === "dropdown") && (
            <>
              <p className="py-2 text-sm">Choices</p>
              <div className="flex flex-col gap-2">
                {choices.map((choice, i) => (
                  <div key={choice.id} className="flex gap-1">
                    <input aria-label={`Choice ${i + 1}`} className="text-input" value={choice.label} onChange={(e) => setChoice(i, e.target.value)} />
                    <button type="button" aria-label={`Remove choice ${i + 1}`} disabled={choices.length <= 1} onClick={() => setProps({ choices: choices.filter((c) => c !== choice) })} className="icon-btn shrink-0 disabled:opacity-30">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
                <button type="button" className="btn-secondary self-start" onClick={() => setProps({ choices: [...choices, { id: crypto.randomUUID().slice(0, 8), label: `Choice ${choices.length + 1}` }] })}>
                  <Plus className="h-4 w-4" /> Add choice
                </button>
              </div>
            </>
          )}
          {type === "multiple_choice" && (
            <div className="mt-2">
              <Toggle label="Multiple selection" checked={!!props.allow_multiple} onChange={(allow_multiple) => setProps({ allow_multiple })} />
              <Toggle label="“Other” option" checked={!!props.allow_other} onChange={(allow_other) => setProps({ allow_other })} />
            </div>
          )}

          {type === "rating" && (
            <div className="grid grid-cols-2 gap-3">
              <Field label="Steps">
                <select className="text-input" value={props.max_rating ?? 5} onChange={(e) => setProps({ max_rating: Number(e.target.value) })}>
                  {[3, 4, 5, 6, 7, 8, 9, 10].map((n) => <option key={n}>{n}</option>)}
                </select>
              </Field>
              <Field label="Icon">
                <select className="text-input" value={props.icon ?? "star"} onChange={(e) => setProps({ icon: e.target.value as QuestionProperties["icon"] })}>
                  <option value="star">Star</option>
                  <option value="heart">Heart</option>
                  <option value="thumbs_up">Thumbs up</option>
                </select>
              </Field>
            </div>
          )}

          {(type === "short_text" || type === "long_text") && (
            <Field label="Max characters">
              <input type="number" min={1} placeholder="0-999999999" className="text-input" value={props.max_length ?? ""} onChange={(e) => setProps({ max_length: e.target.value ? Number(e.target.value) : undefined })} />
            </Field>
          )}

          {type === "number" && (
            <div className="grid grid-cols-2 gap-3">
              {(["min", "max"] as const).map((bound) => (
                <Field key={bound} label={bound === "min" ? "Min number" : "Max number"}>
                  <input type="number" className="text-input" value={props[bound] ?? ""} onChange={(e) => setProps({ [bound]: e.target.value ? Number(e.target.value) : undefined })} />
                </Field>
              ))}
            </div>
          )}

          {type === "contact" &&
            CONTACT_FIELDS.map((field) => {
              const cfg = props.fields?.[field] ?? { enabled: true, required: false };
              const setField = (patch: Partial<typeof cfg>) => setProps({ fields: { ...props.fields, [field]: { ...cfg, ...patch } } });
              return (
                <div key={field} className="border-b border-line py-1 last:border-0">
                  <Toggle label={CONTACT_LABELS[field][0]} checked={cfg.enabled} onChange={(enabled) => setField({ enabled })} />
                  {cfg.enabled && (
                    <div className="pl-4 text-muted">
                      <Toggle label="Required" checked={cfg.required} onChange={(required) => setField({ required })} />
                    </div>
                  )}
                </div>
              );
            })}
        </div>

        {/* Image or video + its layout */}
        <div className="mt-3 border-t border-line pt-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium">Image or video</h3>
            {media.media_url ? (
              <button type="button" aria-label="Remove media" className="icon-btn" onClick={() => setMedia({ media_url: null, media_type: null })}>
                <Trash2 className="h-4 w-4" />
              </button>
            ) : (
              <button type="button" aria-label="Add image or video" aria-expanded={mediaOpen} className="icon-btn border border-line bg-white" onClick={() => setMediaOpen(!mediaOpen)}>
                {mediaOpen ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
              </button>
            )}
          </div>

          {!media.media_url && mediaOpen && (
            <div className="mt-3 flex flex-col gap-2">
              <input
                className="text-input"
                type="url"
                placeholder="Paste an image URL and press Enter"
                aria-label="Image URL"
                onKeyDown={(e) => {
                  const url = e.currentTarget.value.trim();
                  if (e.key === "Enter" && url) setMedia({ media_url: url, media_type: "image" });
                }}
              />
              <button type="button" className="btn-secondary" onClick={() => fileInput.current?.click()}>
                <Upload className="h-4 w-4" /> Upload a file
              </button>
              <input ref={fileInput} type="file" hidden accept="image/*,video/mp4,video/webm" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
            </div>
          )}

          {media.media_url && (
            <>
              {media.media_type === "video" ? (
                <video src={mediaSrc(media.media_url)} className="mt-3 h-28 w-full rounded-lg object-cover" muted />
              ) : (
                // eslint-disable-next-line @next/next/no-img-element -- creator-supplied URL
                <img src={mediaSrc(media.media_url)} alt="" className="mt-3 h-28 w-full rounded-lg object-cover" />
              )}
              <h3 className="mt-4 text-sm font-medium">Layout</h3>
              <Field label="Mobile">
                <select className="text-input" value={media.mobile_orientation} onChange={(e) => setMedia({ mobile_orientation: e.target.value as MediaConfig["mobile_orientation"] })}>
                  <option value="stack">Image on top</option>
                  <option value="wallpaper">Wallpaper</option>
                </select>
              </Field>
              <p className="pb-1.5 pt-2 text-sm">Desktop</p>
              <div role="radiogroup" aria-label="Desktop layout" className="grid grid-cols-3 gap-2">
                {DESKTOP_LAYOUTS.map((layout) => (
                  <button
                    key={layout}
                    type="button"
                    role="radio"
                    aria-checked={media.desktop_orientation === layout}
                    aria-label={layout.replace("_", " ")}
                    title={layout.replace("_", " ")}
                    onClick={() => setMedia({ desktop_orientation: layout })}
                    className={`grid h-10 place-items-center rounded-lg border bg-white ${media.desktop_orientation === layout ? "border-2 border-ink" : "border-line hover:border-muted"}`}
                  >
                    <LayoutIcon layout={layout} />
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {!isScreen(question) && (
        <div className="card p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Logic</h3>
            <button type="button" aria-label="Edit logic" disabled={!canBranch(question)} onClick={onOpenLogic} className="icon-btn border border-line bg-white disabled:opacity-40">
              <Plus className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-1 text-sm text-muted">
            {!canBranch(question)
              ? "Branching is available on Yes/No, Dropdown and single-select Multiple Choice questions."
              : question.logic_jumps.length
                ? `${question.logic_jumps.length} branching rule${question.logic_jumps.length > 1 ? "s" : ""} on this question.`
                : "Send people to different questions based on their answer."}
          </p>
        </div>
      )}

      <div className="card flex items-center justify-between p-5 text-sm">
        <span className="font-medium">Comments</span>
        <span className="rounded-full bg-white px-2 py-0.5 text-xs text-muted">Coming soon</span>
      </div>
    </aside>
  );
}
