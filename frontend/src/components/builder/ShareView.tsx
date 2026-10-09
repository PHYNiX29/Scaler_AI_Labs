"use client";

import { ExternalLink, Link2, Play } from "lucide-react";
import { Form } from "@/types";
import { useToast } from "@/components/ui/Toast";

interface Props {
  form: Form;
  onPublish: () => void;
}

/** "Share" tab: the public link for a published form, plus placeholder embed options. */
export default function ShareView({ form, onPublish }: Props) {
  const toast = useToast();
  const link = `${typeof window === "undefined" ? "" : window.location.origin}/to/${form.slug}`;

  return (
    <div className="card m-4 mt-0 flex-1 overflow-y-auto px-6 py-12">
      <div className="mx-auto max-w-xl">
        <h1 className="text-center text-2xl">Choose how you&apos;d like to share your form</h1>

        {form.status !== "published" ? (
          <div className="mt-10 rounded-2xl bg-white p-8 text-center">
            <p className="text-muted">This form is a draft. Publish it to get a link anyone can open, no login needed.</p>
            <button type="button" className="btn-primary mt-5" onClick={onPublish}>
              <Play className="h-4 w-4" /> Publish
            </button>
          </div>
        ) : (
          <div className="mt-10 rounded-2xl bg-white p-6">
            <div className="flex gap-2">
              <button
                type="button"
                className="btn-primary shrink-0"
                onClick={async () => {
                  await navigator.clipboard.writeText(link);
                  toast("Link copied");
                }}
              >
                <Link2 className="h-4 w-4" /> Copy link
              </button>
              <input readOnly aria-label="Shareable link" value={link} onFocus={(e) => e.target.select()} className="text-input bg-panel" />
              <a href={link} target="_blank" rel="noreferrer" aria-label="Open form in a new tab" className="icon-btn h-auto shrink-0 border border-line px-2">
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
            <p className="mt-6 border-t border-line pt-4 text-sm text-muted">Link preview</p>
            <div className="mt-2 flex items-center gap-4 rounded-xl border border-line p-3">
              <div className="grid h-16 w-28 shrink-0 place-items-center rounded-lg bg-panel text-xs font-semibold">Typeform clone</div>
              <div className="min-w-0">
                <p className="truncate font-medium">{form.title}</p>
                <p className="truncate text-sm text-muted">{form.description || "Turn data collection into an experience."}</p>
              </div>
            </div>
          </div>
        )}

        <h2 className="mt-10 font-semibold">Embed form</h2>
        <div className="mt-3 grid grid-cols-2 gap-4">
          {[
            ["On your website", "#d9b8f2"],
            ["In your email", "#bcdcf7"],
          ].map(([label, color]) => (
            <button key={label} type="button" onClick={() => toast("Embedding is coming soon")} className="flex overflow-hidden rounded-xl bg-white text-left text-sm">
              <span className="h-20 w-28 shrink-0" style={{ background: color }} />
              <span className="p-3">
                {label}
                <span className="mt-1 block text-xs text-muted">Coming soon</span>
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
