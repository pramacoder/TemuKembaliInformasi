"use client";

import { useMemo } from "react";
import { type DocumentType } from "@/lib/api";
import { cn } from "@/lib/utils";

export interface AcademicCoverProps {
  documentId?: string;
  documentType?: DocumentType | string;
  title: string;
  authors?: string[];
  year?: number | null;
  institution?: string | null;
  course?: string | null;
  subtitle?: string | null;
  size?: "sm" | "md" | "lg" | "responsive";
  className?: string;
  variant?: "swiss" | "editorial" | "slate";
}

/**
 * Extracts a 2-digit serial number from document_id or title hash.
 * E.g., "MAT-000008" -> "08", "RES-000001" -> "01"
 */
function extractSequenceNumber(docId?: string, title?: string): string {
  if (docId) {
    const match = docId.match(/(\d{1,4})$/);
    if (match) {
      const num = parseInt(match[1], 10);
      return String(num % 100).padStart(2, "0");
    }
  }
  if (title) {
    let hash = 0;
    for (let i = 0; i < title.length; i++) {
      hash = (hash << 5) - hash + title.charCodeAt(i);
      hash |= 0;
    }
    return String(Math.abs(hash % 99) + 1).padStart(2, "0");
  }
  return "01";
}

export function AcademicCover({
  documentId,
  documentType = "MATERIAL",
  title,
  authors = [],
  year,
  institution,
  course,
  subtitle,
  size = "md",
  className,
  variant = "swiss",
}: AcademicCoverProps) {
  const seqNumber = useMemo(
    () => extractSequenceNumber(documentId, title),
    [documentId, title]
  );

  const docTypeNormalized = (documentType || "MATERIAL").toUpperCase() as DocumentType;

  // Aesthetic subtle accent colors according to document type
  const accentTheme = useMemo(() => {
    switch (docTypeNormalized) {
      case "RESEARCH":
        return {
          pillBg: "bg-slate-900 text-slate-100 dark:bg-slate-100 dark:text-slate-900",
          accentLine: "border-slate-800 dark:border-slate-300",
          accentColor: "text-slate-800 dark:text-slate-200",
          bandBg: "bg-slate-100/80 text-slate-900",
          tagLabel: "RESEARCH PAPER",
          code: "RES",
          tintGradient: "from-slate-50 via-white to-slate-100/50",
        };
      case "THESIS":
        return {
          pillBg: "bg-amber-900 text-amber-50 dark:bg-amber-100 dark:text-amber-950",
          accentLine: "border-amber-700/80 dark:border-amber-400",
          accentColor: "text-amber-800 dark:text-amber-300",
          bandBg: "bg-amber-50/80 text-amber-900",
          tagLabel: "THESIS / DISSERTATION",
          code: "THS",
          tintGradient: "from-amber-50/40 via-white to-stone-100/60",
        };
      case "MATERIAL":
      default:
        return {
          pillBg: "bg-blue-950 text-blue-50 dark:bg-blue-100 dark:text-blue-950",
          accentLine: "border-blue-700/80 dark:border-blue-400",
          accentColor: "text-blue-900 dark:text-blue-300",
          bandBg: "bg-blue-50/80 text-blue-900",
          tagLabel: "COURSE MATERIAL",
          code: "OCW",
          tintGradient: "from-blue-50/30 via-white to-slate-100/60",
        };
    }
  }, [docTypeNormalized]);

  // Dimension classes
  const sizeClasses = {
    sm: "w-28 h-40 text-[9px] p-2.5 shadow-sm rounded-sm",
    md: "w-48 h-64 text-xs p-4 shadow-md rounded-sm",
    lg: "w-64 h-84 text-sm p-6 shadow-xl rounded-md",
    responsive: "w-full aspect-[3/4.2] text-xs p-4 shadow-md rounded-sm",
  }[size];

  const authorDisplay = authors.length > 0 ? authors.slice(0, 2).join(", ") : institution || "Academic IR";

  return (
    <div
      className={cn(
        "relative select-none overflow-hidden transition-all duration-300 group/cover",
        "bg-white dark:bg-zinc-950 border border-zinc-200/90 dark:border-zinc-800",
        "flex flex-col justify-between",
        sizeClasses,
        className
      )}
      style={{
        boxShadow:
          size === "sm"
            ? "1px 2px 6px rgba(0,0,0,0.06), inset 3px 0 6px -2px rgba(0,0,0,0.12)"
            : "2px 6px 18px rgba(0,0,0,0.09), inset 5px 0 10px -3px rgba(0,0,0,0.15)",
      }}
    >
      {/* ── 3D Book Spine & Crease Illusion (Left Edge) ── */}
      <div
        className="absolute left-0 top-0 bottom-0 pointer-events-none z-20"
        style={{
          width: size === "sm" ? "7px" : "12px",
          background:
            "linear-gradient(to right, rgba(0,0,0,0.18) 0%, rgba(0,0,0,0.08) 50%, rgba(0,0,0,0.01) 100%)",
        }}
      />
      <div
        className="absolute top-0 bottom-0 pointer-events-none z-20"
        style={{
          left: size === "sm" ? "8px" : "13px",
          width: "1px",
          backgroundColor: "rgba(255,255,255,0.65)",
        }}
      />

      {/* ── Subtle Background Tint & Architectural Grid Lines ── */}
      <div
        className={cn(
          "absolute inset-0 pointer-events-none opacity-40 bg-gradient-to-b",
          accentTheme.tintGradient
        )}
      />
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.035] dark:opacity-[0.07]"
        style={{
          backgroundImage:
            "radial-gradient(#000 0.75px, transparent 0.75px), radial-gradient(#000 0.75px, #fff 0.75px)",
          backgroundSize: "16px 16px",
          backgroundPosition: "0 0, 8px 8px",
        }}
      />

      {/* ── Top Header: Swiss Numeral (01, 08, etc.) + Series Label ── */}
      <div className="relative z-10 pl-2">
        <div className="flex items-start justify-between">
          <span
            className={cn(
              "font-black tracking-tighter text-zinc-900 dark:text-zinc-50 font-mono leading-none",
              size === "sm" ? "text-2xl" : size === "lg" ? "text-6xl" : "text-4xl"
            )}
          >
            {seqNumber}
          </span>

          <div className="flex flex-col items-end gap-1">
            <span
              className={cn(
                "font-mono font-semibold uppercase tracking-wider text-[8px] px-1.5 py-0.5 rounded-xs",
                accentTheme.pillBg
              )}
            >
              {accentTheme.code}
            </span>
            {year && (
              <span className="font-mono text-[9px] text-zinc-500 dark:text-zinc-400">
                {year}
              </span>
            )}
          </div>
        </div>

        {/* Crisp divider rule (inspired by Pinterest Ref 4) */}
        <div className="mt-2 pt-0.5 border-b-2 border-zinc-900 dark:border-zinc-200" />
      </div>

      {/* ── Mid Section: Type Tag + Title + Description ── */}
      <div className="relative z-10 my-auto py-2 pl-2">
        <p className="font-mono uppercase tracking-widest text-[8px] font-bold text-zinc-500 dark:text-zinc-400 mb-1">
          {course || accentTheme.tagLabel}
        </p>

        <h4
          className={cn(
            "font-bold text-zinc-900 dark:text-zinc-100 tracking-tight leading-snug line-clamp-3 group-hover/cover:text-black transition-colors",
            size === "sm" ? "text-[10px] leading-tight" : size === "lg" ? "text-base" : "text-xs font-extrabold"
          )}
        >
          {title}
        </h4>

        {size !== "sm" && (subtitle || authorDisplay) && (
          <p className="mt-1.5 text-[10px] text-zinc-600 dark:text-zinc-400 line-clamp-2 leading-relaxed">
            {subtitle || authorDisplay}
          </p>
        )}
      </div>

      {/* ── Bottom Section: Divider + Swiss Geometric Monogram + Institution ── */}
      <div className="relative z-10 pl-2">
        <div className="border-t border-zinc-300 dark:border-zinc-800 pt-2 flex items-center justify-between gap-1.5">
          {/* Geometric Monogram Icon (Pinterest Ref 4 style: 3 angled stripes) */}
          <div className="flex items-center gap-1.5 shrink-0">
            <div className="flex items-center -space-x-1 rotate-12">
              <span className="h-3 w-1 rounded-full bg-zinc-400 dark:bg-zinc-600" />
              <span className="h-3.5 w-1 rounded-full bg-zinc-700 dark:bg-zinc-400" />
              <span className="h-4 w-1 rounded-full bg-zinc-900 dark:bg-zinc-100" />
            </div>
            <span className="font-mono text-[8px] font-bold tracking-widest uppercase text-zinc-700 dark:text-zinc-300">
              IR·PUB
            </span>
          </div>

          {/* Publisher / Institution tag */}
          <span className="text-[8px] font-medium text-zinc-500 dark:text-zinc-400 truncate max-w-[100px] text-right">
            {institution || (course ? "OCW UI" : "Academic IR")}
          </span>
        </div>
      </div>
    </div>
  );
}
