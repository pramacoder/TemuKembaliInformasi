"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { type TolerantMetadata } from "@/lib/api";
import { TolerantAuditDialog } from "./tolerant-audit-dialog";
import { HelpCircle, Sparkles, SlidersHorizontal } from "lucide-react";

interface TolerantBannerProps {
  metadata?: TolerantMetadata | null;
  onSearchOriginal: (query: string) => void;
  onApplySuggested: (query: string) => void;
}

export function TolerantBanner({
  metadata,
  onSearchOriginal,
  onApplySuggested,
}: TolerantBannerProps) {
  const [showAudit, setShowAudit] = useState(false);

  if (!metadata) return null;

  const { applied, original_query, effective_query, did_you_mean } = metadata;

  // Case 1: Tolerant retrieval was actively applied (typo / abbreviation resolved)
  if (applied && effective_query.toLowerCase() !== original_query.toLowerCase()) {
    return (
      <>
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-sm">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary shrink-0 animate-pulse" />
              <p className="text-foreground">
                Menampilkan hasil untuk:{" "}
                <strong className="font-semibold text-primary">
                  &ldquo;{effective_query}&rdquo;
                </strong>
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground pl-6">
              <span>Cari</span>
              <button
                type="button"
                onClick={() => onSearchOriginal(original_query)}
                className="font-mono text-primary underline underline-offset-2 hover:text-primary/80 transition-colors"
              >
                &ldquo;{original_query}&rdquo;
              </button>
              <span>sebagai gantinya (tanpa toleransi)</span>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAudit(true)}
              className="h-8 text-xs gap-1.5 border-primary/30 hover:bg-primary/10"
            >
              <SlidersHorizontal className="h-3.5 w-3.5" />
              Lihat Detail Audit
            </Button>
          </div>
        </div>

        <TolerantAuditDialog
          isOpen={showAudit}
          onClose={() => setShowAudit(false)}
          metadata={metadata}
        />
      </>
    );
  }

  // Case 2: Exact search had results, but did_you_mean was detected
  if (!applied && did_you_mean && did_you_mean.toLowerCase() !== original_query.toLowerCase()) {
    return (
      <>
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3.5 flex items-center justify-between gap-3 text-sm">
          <div className="flex items-center gap-2 text-foreground">
            <HelpCircle className="h-4 w-4 text-amber-500 shrink-0" />
            <span>
              Apakah maksud Anda:{" "}
              <button
                type="button"
                onClick={() => onApplySuggested(did_you_mean)}
                className="font-semibold text-primary underline underline-offset-2 hover:opacity-80 transition-opacity"
              >
                &ldquo;{did_you_mean}&rdquo;
              </button>
              ?
            </span>
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowAudit(true)}
            className="h-7 text-xs text-muted-foreground hover:text-foreground"
          >
            Audit Log
          </Button>
        </div>

        <TolerantAuditDialog
          isOpen={showAudit}
          onClose={() => setShowAudit(false)}
          metadata={metadata}
        />
      </>
    );
  }

  return null;
}
