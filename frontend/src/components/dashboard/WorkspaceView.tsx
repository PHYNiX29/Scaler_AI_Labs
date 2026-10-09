"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  BarChart3, Blocks, ChartLine, ChevronDown, CircleHelp, Copy, Gem, LayoutGrid, Link2, List, MoreHorizontal,
  PanelsTopLeft, Pencil, Play, Plus, Search, Square, Trash2, Users, Workflow, X,
} from "lucide-react";
import { Form } from "@/types";
import { api } from "@/lib/api";
import Modal, { ConfirmModal } from "@/components/ui/Modal";
import { Menu, MenuItem } from "@/components/ui/controls";
import { useToast } from "@/components/ui/Toast";

const formatDate = (iso?: string) =>
  iso ? new Date(iso + "Z").toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" }) : "–";

/** The creator's home: every form with its status and response count, plus create / rename / duplicate / delete. */
export default function WorkspaceView() {
  const router = useRouter();
  const toast = useToast();
  const [forms, setForms] = useState<Form[] | null>(null);
  const [search, setSearch] = useState("");
  const [bannerOpen, setBannerOpen] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [renaming, setRenaming] = useState<{ id: string; title: string } | null>(null);
  const [deleting, setDeleting] = useState<Form | null>(null);

  const load = () => api.getForms().then((res) => setForms(res.forms), () => toast("Couldn't load your forms. Is the API running?", "error"));
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load once on mount
  }, []);

  const soon = (what: string) => () => toast(`${what} is coming soon`);

  /** Runs an API call, then refreshes the list and confirms with a toast. */
  const run = async (action: Promise<unknown>, success: string) => {
    try {
      await action;
      toast(success);
      load();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Something went wrong", "error");
    }
  };

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const { form } = await api.createForm(newTitle.trim() || "My new form");
      router.push(`/forms/${form.id}/edit`);
    } catch {
      toast("Couldn't create the form", "error");
    }
  };

  const saveRename = () => {
    if (!renaming) return;
    const title = renaming.title.trim();
    if (title && title !== forms?.find((f) => f.id === renaming.id)?.title) run(api.updateForm(renaming.id, { title }), "Form renamed");
    setRenaming(null);
  };

  const copyLink = async (form: Form) => {
    await navigator.clipboard.writeText(`${window.location.origin}/to/${form.slug}`);
    toast("Link copied");
  };

  const visible = (forms ?? []).filter((f) => f.title.toLowerCase().includes(search.toLowerCase()));
  const totalResponses = (forms ?? []).reduce((sum, f) => sum + f.submissions_count, 0);

  return (
    <div className="flex min-h-dvh min-w-[980px] flex-col px-3 pb-3">
      <header className="flex h-16 items-center justify-between px-2">
        <Link href="/" className="flex items-center gap-2.5 text-sm">
          <span className="h-9 w-2.5 rounded-full bg-ink" />
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-[#b5541c] font-semibold text-white">D</span>
          Demo workspace <ChevronDown className="h-4 w-4" />
        </Link>
        <div className="flex items-center gap-5 text-sm">
          <button type="button" className="flex items-center gap-2" onClick={soon("Integrations")}><Blocks className="h-4 w-4" /> Integrations</button>
          <button type="button" className="flex items-center gap-2" onClick={soon("Brand kit")}><Square className="h-4 w-4" /> Brand kit</button>
          <button type="button" aria-label="Help" onClick={soon("Help center")}><CircleHelp className="h-5 w-5" /></button>
          <span className="grid h-9 w-9 place-items-center rounded-full bg-[#f5cf9a] text-xs font-semibold" title="Demo creator">DC</span>
        </div>
      </header>

      {bannerOpen && (
        <div className="relative mb-3 flex items-center justify-center gap-3 rounded-2xl border border-[#9fd8c9] bg-[#f1faf7] px-4 py-3.5 text-sm">
          <Gem className="h-5 w-5 text-brand-green" />
          <span>You can collect <b>unlimited form responses</b> in this demo.</span>
          <button type="button" className="rounded-md bg-brand-green px-2.5 py-1 text-xs font-semibold text-white" onClick={soon("Plans")}>Get more responses</button>
          <button type="button" aria-label="Dismiss" className="absolute right-8" onClick={() => setBannerOpen(false)}><X className="h-4 w-4" /></button>
        </div>
      )}

      <div className="card flex min-h-0 flex-1 flex-col">
        <nav className="flex items-center gap-2 border-b border-white px-4 pt-3 text-sm">
          <span className="flex items-center gap-2 border-b-2 border-ink px-3 py-3 font-medium"><PanelsTopLeft className="h-4 w-4" /> Forms</span>
          {([["Contacts", Users], ["Automations", Workflow], ["Insights", ChartLine], ["Pages", LayoutGrid]] as const).map(([label, Icon]) => (
            <button key={label} type="button" className="flex items-center gap-2 px-3 py-3 text-ink/80 hover:text-ink" onClick={soon(label)}>
              <Icon className="h-4 w-4" /> {label}
            </button>
          ))}
        </nav>

        <div className="flex min-h-0 flex-1">
          <aside className="flex w-[320px] shrink-0 flex-col border-r border-white">
            <div className="border-b border-white p-5">
              <button type="button" className="btn-primary w-full py-2.5" onClick={() => setCreating(true)}>
                <Plus className="h-4 w-4" /> Create form
              </button>
            </div>
            <label className="flex items-center gap-3 border-b border-white px-9 py-4 text-sm">
              <Search className="h-4 w-4" />
              <input aria-label="Search forms" placeholder="Search" value={search} onChange={(e) => setSearch(e.target.value)} className="w-full bg-transparent outline-none placeholder:text-ink/70" />
            </label>
            <div className="flex-1 p-5 text-sm">
              <div className="flex items-center justify-between px-4 py-2 font-medium">
                <span className="flex items-center gap-2.5"><LayoutGrid className="h-4 w-4" /> Workspaces</span>
                <button type="button" aria-label="New workspace" className="icon-btn border border-line bg-white" onClick={soon("Multiple workspaces")}><Plus className="h-4 w-4" /></button>
              </div>
              <p className="px-4 py-3">Private</p>
              <div className="flex items-center justify-between rounded-lg bg-[#e9e9e9] px-4 py-3">
                My workspace <span className="text-xs">{forms?.length ?? 0}</span>
              </div>
            </div>
            <div className="border-t border-white p-5 text-sm">
              Responses collected
              <div className="mt-2 h-1 rounded-full bg-[#d9d9d9]"><div className="h-full rounded-full bg-ink" style={{ width: totalResponses ? "100%" : 0 }} /></div>
              <p className="mt-2 text-lg">{totalResponses} <span className="text-xs text-muted">total</span></p>
            </div>
          </aside>

          <main className="min-w-0 flex-1 overflow-y-auto p-12 pt-10">
            <div className="flex items-center justify-between border-b border-line pb-6">
              <div className="flex items-center gap-4">
                <h1 className="text-3xl">My workspace</h1>
                <button type="button" className="flex items-center gap-2 text-sm" onClick={soon("Team collaboration")}><Users className="h-4 w-4" /> Invite</button>
              </div>
              <div className="flex overflow-hidden rounded-lg border border-line bg-white text-sm">
                <span className="flex items-center gap-2 bg-[#e9e9e9] px-3 py-2"><List className="h-4 w-4" /> List</span>
                <button type="button" className="flex items-center gap-2 px-3 py-2" onClick={soon("Grid view")}><LayoutGrid className="h-4 w-4" /> Grid</button>
              </div>
            </div>

            {forms === null ? (
              <p className="mt-10 text-sm text-muted">Loading forms…</p>
            ) : visible.length === 0 ? (
              <div className="mt-16 text-center">
                <p className="text-muted">{search ? "No forms match your search." : "You don't have any forms yet."}</p>
                {!search && <button type="button" className="btn-primary mt-4" onClick={() => setCreating(true)}><Plus className="h-4 w-4" /> Create form</button>}
              </div>
            ) : (
              <table className="mt-8 w-full border-separate border-spacing-y-2 text-sm">
                <thead>
                  <tr className="text-ink/80">
                    <th className="pb-2 text-left font-normal" />
                    {["Status", "Questions", "Responses", "Updated"].map((h) => <th key={h} className="px-4 pb-2 text-left font-normal">{h}</th>)}
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {visible.map((form) => (
                    <tr key={form.id} className="group">
                      <td className="rounded-l-xl border-y border-l border-line bg-white p-2.5">
                        <div className="flex items-center gap-4">
                          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-[#b5541c]"><span className="h-5 w-5 rounded bg-[#d9763a]" /></span>
                          {renaming?.id === form.id ? (
                            <input
                              autoFocus
                              aria-label="Form name"
                              className="text-input max-w-xs"
                              value={renaming.title}
                              onChange={(e) => setRenaming({ ...renaming, title: e.target.value })}
                              onBlur={saveRename}
                              onKeyDown={(e) => (e.key === "Enter" ? saveRename() : e.key === "Escape" && setRenaming(null))}
                            />
                          ) : (
                            <Link href={`/forms/${form.id}/edit`} className="truncate font-medium hover:underline">{form.title}</Link>
                          )}
                        </div>
                      </td>
                      <td className="border-y border-line bg-white px-4">
                        <span className={`rounded-full px-2 py-0.5 text-xs ${form.status === "published" ? "bg-[#d9f2e6] text-brand-green" : "bg-panel text-muted"}`}>
                          {form.status === "published" ? "Published" : "Draft"}
                        </span>
                      </td>
                      <td className="border-y border-line bg-white px-4">{form.questions_count ?? "–"}</td>
                      <td className="border-y border-line bg-white px-4">{form.submissions_count || "–"}</td>
                      <td className="border-y border-line bg-white px-4 whitespace-nowrap">{formatDate(form.updated_at)}</td>
                      <td className="rounded-r-xl border-y border-r border-line bg-white pr-2 text-right">
                        <Menu label={`Actions for ${form.title}`} align="right" className="icon-btn ml-auto" button={<MoreHorizontal className="h-4 w-4" />}>
                          <MenuItem onClick={() => router.push(`/forms/${form.id}/edit`)}><Pencil className="h-4 w-4" /> Open</MenuItem>
                          <MenuItem onClick={() => setRenaming({ id: form.id, title: form.title })}><Pencil className="h-4 w-4" /> Rename</MenuItem>
                          <MenuItem onClick={() => run(api.duplicateForm(form.id), "Form duplicated")}><Copy className="h-4 w-4" /> Duplicate</MenuItem>
                          <MenuItem onClick={() => run(api.setPublished(form.id, form.status !== "published"), form.status === "published" ? "Form unpublished" : "Form published")}>
                            <Play className="h-4 w-4" /> {form.status === "published" ? "Unpublish" : "Publish"}
                          </MenuItem>
                          {form.status === "published" && <MenuItem onClick={() => copyLink(form)}><Link2 className="h-4 w-4" /> Copy link</MenuItem>}
                          <MenuItem onClick={() => router.push(`/forms/${form.id}/edit?tab=results`)}><BarChart3 className="h-4 w-4" /> Results</MenuItem>
                          <MenuItem danger onClick={() => setDeleting(form)}><Trash2 className="h-4 w-4" /> Delete</MenuItem>
                        </Menu>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </main>
        </div>
      </div>

      {creating && (
        <Modal title="Create a new form" onClose={() => setCreating(false)}>
          <form onSubmit={create}>
            <label className="block text-sm">
              Give it a name
              <input autoFocus className="text-input mt-1.5" placeholder="My new form" maxLength={255} value={newTitle} onChange={(e) => setNewTitle(e.target.value)} />
            </label>
            <div className="mt-6 flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={() => setCreating(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Continue</button>
            </div>
          </form>
        </Modal>
      )}
      {deleting && (
        <ConfirmModal
          title="Delete this form?"
          message={`“${deleting.title}” and its ${deleting.submissions_count} response${deleting.submissions_count === 1 ? "" : "s"} will be permanently deleted.`}
          confirmLabel="Delete"
          onConfirm={() => run(api.deleteForm(deleting.id), "Form deleted")}
          onClose={() => setDeleting(null)}
        />
      )}
    </div>
  );
}
