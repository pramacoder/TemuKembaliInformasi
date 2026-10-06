"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { type TolerantMetadata } from "@/lib/api";
import {
  ArrowRight,
  HelpCircle,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";

interface TolerantAuditDialogProps {
  isOpen: boolean;
  onClose: () => void;
  metadata: TolerantMetadata | null;
}

export function TolerantAuditDialog({
  isOpen,
  onClose,
  metadata,
}: TolerantAuditDialogProps) {
  if (!metadata) return null;

  const getCorrectionTypeBadge = (type: string) => {
    switch (type) {
      case "typo":
        return <Badge className="bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30">Koreksi Typo</Badge>;
      case "abbreviation":
        return <Badge className="bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30">Ekspansi Singkatan</Badge>;
      case "spelling":
        return <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30">Variasi Ejaan</Badge>;
      case "technical":
        return <Badge className="bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30">Istilah Teknis</Badge>;
      case "cross_lingual":
        return <Badge className="bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 border-indigo-500/30">Lintas Bahasa (ID/EN)</Badge>;
      case "morphological":
        return <Badge className="bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border-cyan-500/30">Variasi Bentuk Kata</Badge>;
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <DialogTitle className="text-base font-semibold">
                Audit Log Tolerant Retrieval
              </DialogTitle>
              <DialogDescription className="text-xs">
                Transparansi &amp; explainability transformasi kueri sebelum tahap retrieval lexical.
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          {/* Query Transformation Overview */}
          <div className="p-3.5 rounded-lg border bg-muted/30 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
              <span className="text-muted-foreground">Mode Eksekusi:</span>
              <span className="font-semibold uppercase tracking-wider text-foreground">
                {metadata.mode === "auto"
                  ? "Otomatis (Exact First + Fallback)"
                  : metadata.mode === "always"
                  ? "Selalu Aktif"
                  : "Nonaktif"}
              </span>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center gap-2 pt-1 border-t">
              <div className="flex-1 min-w-0">
                <p className="text-[11px] text-muted-foreground uppercase tracking-wide">Kueri Asal</p>
                <p className="font-mono text-sm font-semibold truncate text-foreground">
                  {metadata.original_query}
                </p>
              </div>
              <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0 hidden sm:block" />
              <div className="flex-1 min-w-0">
                <p className="text-[11px] text-muted-foreground uppercase tracking-wide">Kueri Efektif (BM25)</p>
                <p className="font-mono text-sm font-semibold truncate text-primary">
                  {metadata.effective_query}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 pt-1 border-t text-xs">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
                <span>
                  Status Fallback:{" "}
                  <strong>{metadata.fallback_triggered ? "Dipicu (Hasil Awal Minim)" : "Normal"}</strong>
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Zap className="h-3.5 w-3.5 text-amber-500" />
                <span>
                  Tingkat Keyakinan: <strong>{Math.round(metadata.confidence * 100)}%</strong>
                </span>
              </div>
            </div>
          </div>

          {/* Transformation details */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Daftar Transformasi Terdeteksi ({metadata.corrections.length})
            </h4>

            {metadata.corrections.length === 0 ? (
              <div className="p-4 text-center border rounded-md text-xs text-muted-foreground">
                Tidak ada perubahan kata. Kueri pengguna sudah sesuai dengan istilah baku atau dokumen dalam indeks.
              </div>
            ) : (
              <div className="space-y-2">
                {metadata.corrections.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 border rounded-lg bg-background flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono line-through text-muted-foreground">
                          {item.source}
                        </span>
                        <ArrowRight className="h-3 w-3 text-muted-foreground" />
                        <span className="font-mono font-semibold text-foreground">
                          {item.target}
                        </span>
                        {getCorrectionTypeBadge(item.type)}
                      </div>
                      {item.note && (
                        <p className="text-[11px] text-muted-foreground">{item.note}</p>
                      )}
                    </div>
                    <div className="shrink-0 flex items-center gap-1 text-[11px] text-muted-foreground">
                      <span>Conf:</span>
                      <strong className="text-foreground">
                        {Math.round(item.confidence * 100)}%
                      </strong>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Expanded terms */}
          {metadata.expanded_terms && metadata.expanded_terms.length > 0 && (
            <div className="space-y-1.5">
              <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Istilah Tambahan / Lintas Bahasa Terhubung
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {metadata.expanded_terms.map((term, i) => (
                  <Badge key={i} variant="secondary" className="font-mono text-xs">
                    {term}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Explanation text */}
          {metadata.explanation && (
            <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-700 dark:text-blue-300 flex items-start gap-2">
              <HelpCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <p>{metadata.explanation}</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
