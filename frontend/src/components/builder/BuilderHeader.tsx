"use client";

import Link from "next/link";
import { ChevronRight, CircleHelp, Link2, PanelsTopLeft, Play } from "lucide-react";
import { Form } from "@/types";
import { useToast } from "@/components/ui/Toast";

export const BUILDER_TABS = ["content", "workflow", "connect", "share", "results"] as const;
export type BuilderTab = (typeof BUILDER_TABS)[number];

interface Props {
  form: Form;
  tab: BuilderTab;
  onTabChange: (tab: BuilderTab) => void;
  onRename: (title: string) => void;
  onSetPublished: (published: boolean) => void;
}

/** Top bar of the builder: breadcrumb with inline rename, section tabs, publish controls. */
export default function BuilderHeader({ form, tab, onTabChange, onRename, onSetPublished }: Props) {
  const toast = useToast();
  const published = form.status === "published";

  const copyLink = async () => {
    if (!published) return toast("Publish the form to get a shareable link", "error");
    await navigator.clipboard.writeText(`${window.location.origin}/to/${form.slug}`);
    toast("Link copied");
  };

  return (
    <header className="grid h-16 shrink-0 grid-cols-[1fr_auto_1fr] items-center gap-4 px-5">
      <div className="flex min-w-0 items-center gap-2 text-sm">
        <Link href="/dashboard" className="flex items-center gap-2 text-muted hover:text-ink">
          <PanelsTopLeft className="h-4 w-4" /> Forms
        </Link>
        <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted" />
        <input
          aria-label="Form name"
          value={form.title}
          onChange={(e) => onRename(e.target.value)}
          className="min-w-0 max-w-64 rounded px-1.5 py-1 hover:bg-panel focus:bg-panel"
        />
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs ${published ? "bg-[#d9f2e6] text-brand-green" : "bg-panel text-muted"}`}>
          {published ? "Published" : "Draft"}
        </span>
      </div>

      <nav className="flex gap-7 text-sm">
        {BUILDER_TABS.map((t) => (
          <button
            key={t}
            type="button"
            aria-current={tab === t ? "page" : undefined}
            onClick={() => onTabChange(t)}
            className={`border-t-2 py-5 capitalize ${tab === t ? "border-ink font-medium" : "border-transparent text-muted hover:text-ink"}`}
          >
            {t}
          </button>
        ))}
      </nav>

      <div className="flex items-center justify-end gap-2">
        {published ? (
          <button type="button" className="btn-secondary" onClick={() => onSetPublished(false)}>
            Unpublish
          </button>
        ) : (
          <button type="button" className="btn-primary" onClick={() => onSetPublished(true)}>
            <Play className="h-4 w-4" /> Publish
          </button>
        )}
        <button type="button" aria-label="Copy form link" onClick={copyLink} className="icon-btn border border-line">
          <Link2 className="h-4 w-4" />
        </button>
        <button type="button" onClick={() => toast("Plans are coming soon")} className="rounded-lg bg-brand-green px-3.5 py-2 text-sm font-semibold text-white">
          View plans
        </button>
        <button type="button" aria-label="Help" onClick={() => toast("Help center is coming soon")} className="icon-btn">
          <CircleHelp className="h-5 w-5" />
        </button>
        <span className="grid h-9 w-9 place-items-center rounded-full bg-[#f5cf9a] text-xs font-semibold" title="Demo creator">
          DC
        </span>
      </div>
    </header>
  );
}
