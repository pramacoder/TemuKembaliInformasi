"use client";

import { cn } from "@/lib/utils";
import { type DocumentType } from "@/lib/api";

export interface CoverSpineProps {
  documentId: string;
  title: string;
  authors?: string[];
  year?: number | null;
  documentType?: DocumentType | string;
  institution?: string | null;
  colorScheme?: "obsidian" | "navy" | "amber" | "charcoal" | "sage";
  onClick?: () => void;
  className?: string;
}

export function CoverSpine({
  documentId,
  title,
  year,
  documentType = "MATERIAL",
  institution,
  colorScheme = "obsidian",
  onClick,
  className,
}: CoverSpineProps) {
  // Color presets for the leather/cloth spine binding
  const styles = {
    obsidian: {
      bg: "bg-gradient-to-r from-zinc-900 via-zinc-800 to-zinc-950 text-zinc-100",
      accent: "border-amber-400/50 text-amber-300",
      band: "bg-amber-400/20",
      tag: "OCW",
    },
    navy: {
      bg: "bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-950 text-slate-100",
      accent: "border-sky-400/50 text-sky-300",
      band: "bg-sky-400/20",
      tag: "RES",
    },
    amber: {
      bg: "bg-gradient-to-r from-stone-900 via-amber-950 to-stone-950 text-amber-50",
      accent: "border-amber-500/50 text-amber-400",
      band: "bg-amber-500/25",
      tag: "THS",
    },
    charcoal: {
      bg: "bg-gradient-to-r from-neutral-900 via-neutral-800 to-neutral-950 text-neutral-100",
      accent: "border-zinc-400/50 text-zinc-300",
      band: "bg-zinc-400/20",
      tag: "IR",
    },
    sage: {
      bg: "bg-gradient-to-r from-emerald-950 via-teal-900 to-emerald-950 text-emerald-50",
      accent: "border-emerald-400/50 text-emerald-300",
      band: "bg-emerald-400/20",
      tag: "ACM",
    },
  }[colorScheme];

  // Extract short volume / serial
  const volMatch = documentId.match(/\d+$/);
  const volNumber = volMatch ? volMatch[0].slice(-2) : "01";

  return (
    <div
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onClick?.()}
      className={cn(
        "group/spine relative flex flex-col justify-between items-center cursor-pointer",
        "w-11 sm:w-13 h-64 sm:h-72 select-none",
        "rounded-t-sm transition-all duration-300 ease-out",
        "hover:-translate-y-6 hover:shadow-2xl hover:z-30",
        "border-x border-t border-black/30",
        styles.bg,
        className
      )}
      style={{
        boxShadow: "inset 2px 0 5px rgba(255,255,255,0.08), inset -2px 0 5px rgba(0,0,0,0.5), 0 4px 10px rgba(0,0,0,0.3)",
      }}
    >
      {/* ── Top Foil Accent Band ── */}
      <div className="w-full pt-3 pb-2 flex flex-col items-center">
        <div className="w-4/5 h-[1.5px] bg-amber-400/60 mb-1" />
        <span className="font-mono text-[9px] font-black tracking-widest text-amber-300/90">
          VOL.{volNumber}
        </span>
        <div className="w-4/5 h-[1.5px] bg-amber-400/60 mt-1" />
      </div>

      {/* ── Vertical Spine Title (Rotated 90 deg) ── */}
      <div className="flex-1 w-full flex items-center justify-center overflow-hidden py-2 px-1">
        <p
          className="text-[11px] sm:text-xs font-semibold tracking-wider text-zinc-200 group-hover/spine:text-amber-200 transition-colors uppercase whitespace-nowrap line-clamp-1"
          style={{
            writingMode: "vertical-rl",
            transform: "rotate(180deg)",
            maxHeight: "150px",
            letterSpacing: "0.08em",
          }}
        >
          {title}
        </p>
      </div>

      {/* ── Bottom Section: Year & Publisher Crest ── */}
      <div className="w-full pb-3 pt-2 flex flex-col items-center">
        <div className="w-4/5 h-[1px] bg-white/20 mb-1" />
        <span className="font-mono text-[8px] text-zinc-400 font-medium">
          {year || "2024"}
        </span>
        <div className="mt-1 flex items-center gap-0.5 opacity-80">
          <div className="h-1.5 w-1.5 rounded-full bg-amber-400/70" />
        </div>
      </div>

      {/* ── Hover Tooltip Card ── */}
      <div className="absolute -top-16 left-1/2 -translate-x-1/2 opacity-0 group-hover/spine:opacity-100 pointer-events-none transition-all duration-200 bg-zinc-900 text-zinc-100 text-[11px] px-3 py-1.5 rounded-md shadow-2xl whitespace-nowrap z-50 border border-zinc-700/80">
        <p className="font-semibold line-clamp-1 max-w-[180px]">{title}</p>
        <p className="text-[10px] text-zinc-400">Klik untuk membaca</p>
      </div>
    </div>
  );
}
