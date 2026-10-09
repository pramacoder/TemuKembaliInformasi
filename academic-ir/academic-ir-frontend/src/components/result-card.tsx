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
import { Calendar, ExternalLink, FileText, Globe, Layers, Tag, Users, Sparkles } from "lucide-react";
import { SummaryDialog } from "@/components/summary-dialog";

interface ResultCardProps {
  result: SearchResult;
  activeQuery?: string;
}

export function ResultCard({ result, activeQuery = "" }: ResultCardProps) {
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);

  // Qualitative relevance label (expert plan §19)
  const score = result.relevance_score;
  let relevanceLabel = "Kurang Relevan";
  let labelBadgeClass = "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";

  if (score >= 0.80) {
    relevanceLabel = "Sangat Relevan";
    labelBadgeClass = "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border-emerald-300";
  } else if (score >= 0.60) {
    relevanceLabel = "Relevan";
    labelBadgeClass = "bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300 border-blue-300";
  } else if (score >= 0.40) {
    relevanceLabel = "Cukup Relevan";
    labelBadgeClass = "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border-amber-300";
  }

  // Provenance label
  const provenanceLabel =
    result.source === "OCW_UI"
      ? "OCW UI (Benchmark)"
      : result.source === "CORE"
        ? "CORE Open Access"
        : result.source === "DOAJ"
          ? "DOAJ Open Journal"
          : result.source === "REPOSITORY"
            ? "Repository Kampus"
            : result.source;

  const openUrl = result.source_url ?? null;

  // Page range
  const pageDisplay =
    result.best_page_start && result.best_page_end && result.best_page_start !== result.best_page_end
      ? `Hal. ${result.best_page_start}–${result.best_page_end}`
      : result.best_page_start || result.page
        ? `Hal. ${result.best_page_start || result.page}`
        : null;

  return (
    <Card className="group transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          {/* Rank + Title */}
          <div className="flex items-start gap-3 min-w-0">
            <span className="shrink-0 mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-semibold text-muted-foreground">
              {result.rank}
            </span>
            <div className="min-w-0">
              <h3 className="text-base font-semibold leading-snug text-foreground group-hover:text-primary transition-colors line-clamp-2">
                {result.title}
              </h3>
            </div>
          </div>

          {/* Qualitative Score Badge with numerical tooltip */}
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

        {/* Metadata row */}
        <div className="ml-9 flex flex-wrap items-center gap-2 mt-2">
          <Badge
            className={cn(
              "text-xs font-medium border-0",
              DOCUMENT_TYPE_COLORS[result.document_type]
            )}
          >
            {DOCUMENT_TYPE_LABELS[result.document_type]}
          </Badge>

          {/* Provenance Badge */}
          <Badge variant="outline" className="text-xs text-muted-foreground">
            {provenanceLabel}
          </Badge>

          {result.year && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              {result.year}
            </span>
          )}

          {result.chunk_count && result.chunk_count > 1 && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Layers className="h-3 w-3" />
              {result.chunk_count} bagian cocok
            </span>
          )}

          {result.institution && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground truncate max-w-[200px]">
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
      </CardHeader>

      <CardContent className="pt-0 ml-9 space-y-3">
        {/* Authors */}
        {result.authors.length > 0 && (
          <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <Users className="h-3.5 w-3.5 shrink-0" />
            {result.authors.join(", ")}
          </p>
        )}

        {result.course && (
          <p className="text-xs text-muted-foreground">
            <span className="font-medium">Mata Kuliah:</span> {result.course}
          </p>
        )}

        <Separator />

        {/* Snippet */}
        {result.snippet ? (
          <p className="text-sm text-foreground/80 leading-relaxed line-clamp-4">
            {result.snippet}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground italic">Pratinjau tidak tersedia.</p>
        )}

        {/* Keywords */}
        {result.keywords.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <Tag className="h-3 w-3 text-muted-foreground shrink-0" />
            {result.keywords.slice(0, 6).map((kw) => (
              <Badge key={kw} variant="outline" className="text-xs px-1.5 py-0 h-5">
                {kw}
              </Badge>
            ))}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-1 flex-wrap">
          {openUrl ? (
            <Button
              size="sm"
              className="h-7 text-xs gap-1.5"
              onClick={() => window.open(openUrl, "_blank")}
            >
              <ExternalLink className="h-3 w-3" />
              Buka Dokumen
            </Button>
          ) : (
            <Button size="sm" variant="outline" className="h-7 text-xs" disabled>
              URL tidak tersedia
            </Button>
          )}

          <Button
            size="sm"
            variant="secondary"
            className="h-7 text-xs gap-1.5 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 font-medium"
            onClick={() => setIsSummaryOpen(true)}
          >
            <Sparkles className="h-3 w-3" />
            Ringkasan
          </Button>

          {pageDisplay && (
            <span className="text-xs text-muted-foreground font-medium">{pageDisplay}</span>
          )}
          {result.doi && (
            <span className="text-xs text-muted-foreground font-mono truncate max-w-[160px]">
              {result.doi}
            </span>
          )}
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
      </CardContent>
    </Card>
  );
}
