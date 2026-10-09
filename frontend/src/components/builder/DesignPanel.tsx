"use client";

import { X } from "lucide-react";
import { ThemeSettings } from "@/types";
import { Field } from "@/components/ui/controls";

const PRESETS: Record<string, ThemeSettings> = {
  Default: { font_family: "Inter", background_color: "#FAFAFA", text_color: "#262627", button_color: "#262627", button_text_color: "#FFFFFF" },
  Plum: { font_family: "Georgia", background_color: "#F6F1F7", text_color: "#3A2E3D", button_color: "#7B3FA0", button_text_color: "#FFFFFF" },
  Ocean: { font_family: "Inter", background_color: "#EEF6FB", text_color: "#0F2B46", button_color: "#0B6FB8", button_text_color: "#FFFFFF" },
  Midnight: { font_family: "Inter", background_color: "#16161D", text_color: "#F3F3F5", button_color: "#F3F3F5", button_text_color: "#16161D" },
};
const FONTS = ["Inter", "Georgia", "Courier New", "Trebuchet MS", "Verdana"];
const COLORS: [keyof ThemeSettings, string][] = [
  ["background_color", "Background"],
  ["text_color", "Questions and answers"],
  ["button_color", "Buttons"],
  ["button_text_color", "Button text"],
];

interface Props {
  theme: ThemeSettings;
  onChange: (theme: ThemeSettings) => void;
  onClose: () => void;
}

/** Form-wide theme editor; replaces the question settings while "Design" is open. */
export default function DesignPanel({ theme, onChange, onClose }: Props) {
  return (
    <aside className="card h-full w-[320px] shrink-0 overflow-y-auto p-5">
      <div className="flex items-center justify-between">
        <h2 className="font-medium">Design</h2>
        <button type="button" aria-label="Close design panel" onClick={onClose} className="icon-btn">
          <X className="h-4 w-4" />
        </button>
      </div>

      <p className="pb-2 pt-4 text-sm">Themes</p>
      <div className="grid grid-cols-2 gap-2">
        {Object.entries(PRESETS).map(([name, preset]) => (
          <button
            key={name}
            type="button"
            onClick={() => onChange(preset)}
            className="rounded-lg border border-line p-3 text-left text-sm hover:border-muted"
            style={{ background: preset.background_color, color: preset.text_color, fontFamily: preset.font_family }}
          >
            {name}
            <span className="mt-2 block h-2 w-8 rounded" style={{ background: preset.button_color }} />
          </button>
        ))}
      </div>

      <div className="mt-4 border-t border-line pt-2">
        <Field label="Font">
          <select className="text-input" value={theme.font_family} onChange={(e) => onChange({ ...theme, font_family: e.target.value })}>
            {FONTS.map((font) => <option key={font}>{font}</option>)}
          </select>
        </Field>
        {COLORS.map(([key, label]) => (
          <label key={key} className="flex items-center justify-between py-2 text-sm">
            {label}
            <input type="color" className="h-8 w-10 cursor-pointer rounded border border-line bg-white" value={theme[key]} onChange={(e) => onChange({ ...theme, [key]: e.target.value })} />
          </label>
        ))}
      </div>
    </aside>
  );
}
