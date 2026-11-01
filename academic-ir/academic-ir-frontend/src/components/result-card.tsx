"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import {
  DOCUMENT_TYPE_COLORS,
  DOCUMENT_TYPE_LABELS,
  type SearchResult,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  Calendar,
  ExternalLink,
  FileText,
  Globe,
  Layers,
  Tag,
  Users,
  Sparkles,
  BookOpen,
} from "lucide-react";
import { SummaryDialog } from "@/components/summary-dialog";
import { DocumentReaderDialog } from "@/components/document-reader-dialog";
import { AcademicCover } from "@/components/covers/academic-cover";

interface ResultCardProps {
  result: SearchResult;
  activeQuery?: string;
  viewMode?: "list" | "grid";
}

export function ResultCard({
  result,
  activeQuery = "",
  viewMode = "list",
}: ResultCardProps) {
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [isReaderOpen, setIsReaderOpen] = useState(false);

  // Qualitative relevance label
  const score = result.relevance_score;
  let relevanceLabel = "Kurang Relevan";
  let labelBadgeClass = "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";

  if (score >= 0.8) {
    relevanceLabel = "Sangat Relevan";
    labelBadgeClass =
      "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border-emerald-300";
  } else if (score >= 0.6) {
    relevanceLabel = "Relevan";
    labelBadgeClass =
      "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border-blue-300";
  } else if (score >= 0.4) {
    relevanceLabel = "Cukup Relevan";
    labelBadgeClass =
      "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border-amber-300";
  }

  // Provenance label
  const provenanceLabel =
    result.source === "OCW_UI"
      ? "OCW UI (Benchmark)"
      : result.source === "CORE"
      ? "CORE Open Access"
      : result.source === "DOAJ"
      ? "DOAJ Open Journal"
      : result.source === "REPOSITORY" || result.source === "Institutional Repository"
      ? "Repository Kampus"
      : result.source;

  const openUrl = result.source_url ?? null;

  // Page range
  const pageDisplay =
    result.best_page_start &&
    result.best_page_end &&
    result.best_page_start !== result.best_page_end
      ? `Hal. ${result.best_page_start}–${result.best_page_end}`
      : result.best_page_start || result.page
      ? `Hal. ${result.best_page_start || result.page}`
      : null;

  // ─── GRID VIEW (Pinterest Ref 2 & 4 style) ───
  if (viewMode === "grid") {
    return (
      <Card className="group flex flex-col justify-between overflow-hidden transition-all duration-200 hover:shadow-xl hover:-translate-y-1 border-zinc-200/90 dark:border-zinc-800">
        <div className="p-4 bg-zinc-50/60 dark:bg-zinc-900/40 flex justify-center items-center border-b border-zinc-100 dark:border-zinc-800">
          <div
            onClick={() => setIsReaderOpen(true)}
            className="cursor-pointer transition-transform duration-200 group-hover:scale-102"
          >
            <AcademicCover
              documentId={result.document_id}
              documentType={result.document_type}
              title={result.title}
              authors={result.authors}
              year={result.year}
              institution={result.institution}
              course={result.course}
              size="md"
            />
          </div>
        </div>

        <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <span className={cn("text-[10px] font-medium px-2 py-0.5 rounded-full border", labelBadgeClass)}>
                {relevanceLabel} ({score.toFixed(2)})
              </span>
              <span className="font-mono text-xs text-muted-foreground">#{result.rank}</span>
            </div>

            <h3
              onClick={() => setIsReaderOpen(true)}
              className="text-sm font-bold text-foreground leading-snug line-clamp-2 cursor-pointer group-hover:text-primary transition-colors"
            >
              {result.title}
            </h3>

            {result.snippet && (
              <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed italic">
                "{result.snippet}"
              </p>
            )}
          </div>

          <div className="pt-2 border-t border-zinc-100 dark:border-zinc-800 flex items-center gap-1.5">
            <Button
              size="sm"
              className="flex-1 h-7 text-xs gap-1"
              onClick={() => setIsReaderOpen(true)}
            >
              <BookOpen className="h-3 w-3" />
              Baca
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs gap-1"
              onClick={() => setIsSummaryOpen(true)}
            >
              <Sparkles className="h-3 w-3 text-amber-500" />
              AI
            </Button>
          </div>
        </div>

        <SummaryDialog
          isOpen={isSummaryOpen}
          onClose={() => setIsSummaryOpen(false)}
          documentId={result.document_id}
          documentTitle={result.title}
          activeQuery={activeQuery}
          documentType={result.document_type}
        />

        <DocumentReaderDialog
          isOpen={isReaderOpen}
          onClose={() => setIsReaderOpen(false)}
          documentId={result.document_id}
          initialPage={result.best_page_start || result.page || 1}
          activeQuery={activeQuery}
          onOpenSummary={() => {
            setIsReaderOpen(false);
            setIsSummaryOpen(true);
          }}
        />
      </Card>
    );
  }

  // ─── LIST VIEW WITH SWISS COVER THUMBNAIL (Default) ───
  return (
    <Card className="group transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 border-zinc-200/90 dark:border-zinc-800">
      <div className="p-4 sm:p-5 flex flex-col sm:flex-row gap-4 items-start">
        
        {/* Left Side: Minimalist Swiss Academic Cover Thumbnail */}
        <div
          onClick={() => setIsReaderOpen(true)}
          className="shrink-0 cursor-pointer transition-transform duration-200 group-hover:scale-102 hidden sm:block"
        >
          <AcademicCover
            documentId={result.document_id}
            documentType={result.document_type}
            title={result.title}
            authors={result.authors}
            year={result.year}
            institution={result.institution}
            course={result.course}
            size="sm"
          />
        </div>

        {/* Right Side: Main Detail & Actions */}
        <div className="flex-1 min-w-0 space-y-3">
          
          {/* Header Row: Rank + Title + Relevance Badge */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-2.5 min-w-0">
              <span className="shrink-0 mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-muted font-mono text-xs font-bold text-muted-foreground">
                {result.rank}
              </span>
              <div className="min-w-0">
                <h3
                  onClick={() => setIsReaderOpen(true)}
                  className="text-base font-bold leading-snug text-foreground group-hover:text-primary transition-colors line-clamp-2 cursor-pointer"
                >
                  {result.title}
                </h3>
              </div>
            </div>

            <Tooltip>
              <TooltipTrigger asChild>
                <div className="shrink-0 flex flex-col items-end cursor-help">
                  <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full border", labelBadgeClass)}>
                    {relevanceLabel}
                  </span>
                  <span className="text-[11px] text-muted-foreground font-mono mt-0.5 tabular-nums">
                    {score.toFixed(4)}
                  </span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>Relevance score: {score.toFixed(6)}</p>
                {result.aggregation_strategy && (
                  <p className="text-xs text-muted-foreground">Strategi: {result.aggregation_strategy}</p>
                )}
              </TooltipContent>
            </Tooltip>
          </div>

          {/* Metadata Badges */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <Badge className={cn("text-xs font-medium border-0", DOCUMENT_TYPE_COLORS[result.document_type])}>
              {DOCUMENT_TYPE_LABELS[result.document_type]}
            </Badge>

            <Badge variant="outline" className="text-xs text-muted-foreground">
              {provenanceLabel}
            </Badge>

            {result.year && (
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Calendar className="h-3 w-3" />
                {result.year}
              </span>
            )}

            {result.matched_pages && result.matched_pages.length > 0 ? (
              <span className="flex items-center gap-1 text-xs text-primary font-medium bg-primary/10 px-2 py-0.5 rounded-full border border-primary/20">
                <Layers className="h-3 w-3" />
                Relevan di Hal. {result.matched_pages.slice(0, 4).join(", ")}
                {result.matched_pages.length > 4 ? "..." : ""}
              </span>
            ) : result.chunk_count && result.chunk_count > 1 ? (
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Layers className="h-3 w-3" />
                {result.chunk_count} bagian relevan
              </span>
            ) : null}

            {result.institution && (
              <span className="flex items-center gap-1 text-xs text-muted-foreground truncate max-w-[180px]">
                <FileText className="h-3 w-3 shrink-0" />
                <span className="truncate">{result.institution}</span>
              </span>
            )}

            {result.language && (
              <span className="flex items-center gap-1 text-xs text-muted-foreground uppercase">
                <Globe className="h-3 w-3" />
                {result.language}
              </span>
            )}
          </div>

          {/* Authors */}
          {result.authors.length > 0 && (
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Users className="h-3.5 w-3.5 shrink-0" />
              {result.authors.join(", ")}
            </p>
          )}

          {result.course && (
            <p className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">Mata Kuliah:</span> {result.course}
            </p>
          )}

          {/* Snippet / Abstract Preview */}
          {result.abstract ? (
            <div className="space-y-0.5 bg-zinc-50/70 dark:bg-zinc-900/50 p-2.5 rounded-md border border-zinc-100 dark:border-zinc-800">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-primary/80 flex items-center gap-1">
                <FileText className="h-3 w-3" />
                Abstrak Dokumen
              </span>
              <p className="text-xs text-foreground/85 leading-relaxed line-clamp-3">
                {result.abstract}
              </p>
            </div>
          ) : result.snippet ? (
            <div className="space-y-0.5 bg-zinc-50/70 dark:bg-zinc-900/50 p-2.5 rounded-md border border-zinc-100 dark:border-zinc-800">
              <span className="text-[10px] font-medium text-muted-foreground flex items-center gap-1">
                <FileText className="h-3 w-3" />
                Cuplikan Halaman Terkait ({pageDisplay || "Bagian Relevan"}):
              </span>
              <p className="text-xs text-foreground/80 leading-relaxed line-clamp-3 italic">
                "{result.snippet}"
              </p>
            </div>
          ) : null}

          {/* Keywords */}
          {result.keywords.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5">
              <Tag className="h-3 w-3 text-muted-foreground shrink-0" />
              {result.keywords.slice(0, 6).map((kw) => (
                <Badge key={kw} variant="outline" className="text-[10px] px-1.5 py-0 h-4.5">
                  {kw}
                </Badge>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2 pt-1 flex-wrap">
            <Button
              size="sm"
              className="h-7 text-xs gap-1.5 font-medium shadow-xs"
              onClick={() => setIsReaderOpen(true)}
            >
              <BookOpen className="h-3 w-3" />
              Baca Dokumen Lengkap
            </Button>

            <Button
              size="sm"
              variant="secondary"
              className="h-7 text-xs gap-1.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 font-medium"
              onClick={() => setIsSummaryOpen(true)}
            >
              <Sparkles className="h-3 w-3" />
              Ringkasan AI
            </Button>

            {openUrl && (
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1.5 text-muted-foreground hover:text-foreground"
                onClick={() => window.open(openUrl, "_blank")}
              >
                <ExternalLink className="h-3 w-3" />
                Tautan Luar
              </Button>
            )}

            {pageDisplay && (
              <span className="text-xs text-muted-foreground font-medium ml-auto">{pageDisplay}</span>
            )}
          </div>
        </div>
      </div>

      {/* Modal Dialog for Summarization */}
      <SummaryDialog
        isOpen={isSummaryOpen}
        onClose={() => setIsSummaryOpen(false)}
        documentId={result.document_id}
        documentTitle={result.title}
        activeQuery={activeQuery}
        documentType={result.document_type}
      />

      {/* Full Document Reader Dialog */}
      <DocumentReaderDialog
        isOpen={isReaderOpen}
        onClose={() => setIsReaderOpen(false)}
        documentId={result.document_id}
        initialPage={result.best_page_start || result.page || 1}
        activeQuery={activeQuery}
        onOpenSummary={() => {
          setIsReaderOpen(false);
          setIsSummaryOpen(true);
        }}
      />
    </Card>
  );
}
