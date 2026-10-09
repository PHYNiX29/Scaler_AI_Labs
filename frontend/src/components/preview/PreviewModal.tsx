"use client";

import { useEffect, useState } from "react";
import { Monitor, RotateCcw, Smartphone, X } from "lucide-react";
import { Form } from "@/types";
import RespondentFlow from "@/components/respondent/RespondentFlow";

/** Full-screen live preview of the form being built. Nothing is submitted to the server. */
export default function PreviewModal({ form, onClose }: { form: Form; onClose: () => void }) {
  const [mobile, setMobile] = useState(false);
  const [run, setRun] = useState(0); // bumping the key restarts the flow from the first page

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div role="dialog" aria-modal="true" aria-label="Form preview" className="fixed inset-0 z-50 flex flex-col items-center gap-5 bg-white p-5">
      <div className="card flex items-center gap-1 p-1">
        <button type="button" aria-label="Close preview" className="icon-btn" onClick={onClose}>
          <X className="h-4 w-4" />
        </button>
        <button type="button" aria-label={mobile ? "Switch to desktop preview" : "Switch to mobile preview"} className="icon-btn" onClick={() => setMobile(!mobile)}>
          {mobile ? <Monitor className="h-4 w-4" /> : <Smartphone className="h-4 w-4" />}
        </button>
        <button type="button" aria-label="Restart preview" className="icon-btn" onClick={() => setRun(run + 1)}>
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>
      <div className={`min-h-0 w-full flex-1 overflow-hidden border border-line shadow-sm transition-[max-width] duration-300 ${mobile ? "max-w-[390px] rounded-3xl" : "max-w-6xl"}`}>
        <RespondentFlow key={run} form={form} isPreview />
      </div>
    </div>
  );
}
