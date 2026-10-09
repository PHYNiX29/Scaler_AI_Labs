"use client";

import { useEffect, useRef, useState } from "react";

/** Typeform-style on/off switch with its label on the left. */
export function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (on: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 py-2 text-sm">
      {label}
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={`flex h-[18px] w-8 shrink-0 items-center rounded-full p-0.5 transition-colors ${
          checked ? "justify-end bg-plum" : "justify-start bg-[#d4d4d4]"
        }`}
      >
        <span className="h-3.5 w-3.5 rounded-full bg-white" />
      </button>
    </label>
  );
}

/** A labelled form control stacked vertically. */
export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block py-2 text-sm">
      <span className="mb-1.5 block">{label}</span>
      {children}
    </label>
  );
}

/** A button that opens a small floating menu; closes on outside click, Escape, or picking an item. */
export function Menu({
  button,
  children,
  align = "left",
  label,
  className = "",
}: {
  button: React.ReactNode;
  children: React.ReactNode;
  align?: "left" | "right";
  label: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent | KeyboardEvent) => {
      if (e instanceof KeyboardEvent ? e.key === "Escape" : !ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", close);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", close);
    };
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button type="button" aria-haspopup="menu" aria-expanded={open} aria-label={label} onClick={() => setOpen(!open)} className={className}>
        {button}
      </button>
      {open && (
        <div
          role="menu"
          onClick={() => setOpen(false)}
          className={`pop-in absolute top-full z-40 mt-1 min-w-48 rounded-xl border border-line bg-white p-1.5 shadow-xl ${
            align === "right" ? "right-0" : "left-0"
          }`}
        >
          {children}
        </div>
      )}
    </div>
  );
}

export function MenuItem({ onClick, children, danger }: { onClick: () => void; children: React.ReactNode; danger?: boolean }) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onClick}
      className={`flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-left text-sm hover:bg-panel ${danger ? "text-[#c0392b]" : ""}`}
    >
      {children}
    </button>
  );
}
