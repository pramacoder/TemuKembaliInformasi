"use client";

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
import { BookOpen, Calendar, ExternalLink, FileText, Globe, Tag, Users } from "lucide-react";

interface ResultCardProps {
  result: SearchResult;
}

export function ResultCard({ result }: ResultCardProps) {
  const scorePercent = Math.round(result.relevance_score * 100);
  const scoreColor =
    result.relevance_score >= 0.5
      ? "text-emerald-600 dark:text-emerald-400"
      : result.relevance_score >= 0.2
        ? "text-amber-600 dark:text-amber-400"
        : "text-muted-foreground";

  const openUrl = result.source_url ?? null;

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

          {/* Relevance Score */}
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="shrink-0 flex flex-col items-center cursor-help">
                <span className={cn("text-lg font-bold tabular-nums leading-none", scoreColor)}>
                  {scorePercent}
                </span>
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide">score</span>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>Cosine similarity: {result.relevance_score.toFixed(6)}</p>
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

          {result.year && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              {result.year}
            </span>
          )}

          <span className="flex items-center gap-1 text-xs text-muted-foreground truncate max-w-[200px]">
            <BookOpen className="h-3 w-3 shrink-0" />
            <span className="truncate">{result.source}</span>
          </span>

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
            <span className="font-medium">Course:</span> {result.course}
          </p>
        )}

        <Separator />

        {/* Snippet */}
        {result.snippet ? (
          <p className="text-sm text-foreground/80 leading-relaxed line-clamp-4">
            {result.snippet}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground italic">No preview available.</p>
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
        <div className="flex items-center gap-2 pt-1">
          {openUrl ? (
            <Button
              size="sm"
              className="h-7 text-xs gap-1.5"
              onClick={() => window.open(openUrl, "_blank")}
            >
              <ExternalLink className="h-3 w-3" />
              Open Document
            </Button>
          ) : (
            <Button size="sm" variant="outline" className="h-7 text-xs" disabled>
              No URL available
            </Button>
          )}
          {result.page && (
            <span className="text-xs text-muted-foreground">p.{result.page}</span>
          )}
          {result.doi && (
            <span className="text-xs text-muted-foreground font-mono truncate max-w-[160px]">
              {result.doi}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
