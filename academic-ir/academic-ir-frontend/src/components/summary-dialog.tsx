"use client";

import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  fetchDocumentSummary,
  fetchQuerySummary,
  type SummaryResponse,
} from "@/lib/api";
import {
  Sparkles,
  BookOpen,
  Copy,
  Check,
  RefreshCw,
  Search,
  Zap,
  AlertCircle,
  FileText,
  Clock,
} from "lucide-react";

interface SummaryDialogProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: string;
  documentTitle: string;
  activeQuery?: string;
  documentType?: string;
}

export function SummaryDialog({
  isOpen,
  onClose,
  documentId,
  documentTitle,
  activeQuery = "",
  documentType,
}: SummaryDialogProps) {
  const [activeTab, setActiveTab] = useState<"doc" | "query">("doc");

  // State for Document Summary
  const [docSummary, setDocSummary] = useState<SummaryResponse | null>(null);
  const [docLoading, setDocLoading] = useState(false);
  const [docError, setDocError] = useState<string | null>(null);

  // State for Query Summary
  const [querySummary, setQuerySummary] = useState<SummaryResponse | null>(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  const [copied, setCopied] = useState(false);

  // Load document summary on open
  useEffect(() => {
    if (!isOpen || !documentId) return;

    loadDocSummary(false);

    if (activeQuery.trim()) {
      loadQuerySummary(false);
    } else {
      setQuerySummary(null);
    }
  }, [isOpen, documentId]);

  const loadDocSummary = async (forceRefresh = false) => {
    setDocLoading(true);
    setDocError(null);
    try {
      const res = await fetchDocumentSummary(documentId, 4, forceRefresh);
      setDocSummary(res);
    } catch (err: any) {
      setDocError(err?.message ?? "Gagal memuat ringkasan dokumen");
    } finally {
      setDocLoading(false);
    }
  };

  const loadQuerySummary = async (forceRefresh = false) => {
    if (!activeQuery.trim()) return;
    setQueryLoading(true);
    setQueryError(null);
    try {
      const res = await fetchQuerySummary(documentId, activeQuery, 4, forceRefresh);
      setQuerySummary(res);
    } catch (err: any) {
      setQueryError(err?.message ?? "Gagal memuat ringkasan relevan");
    } finally {
      setQueryLoading(false);
    }
  };

  const handleCopy = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatLanguageLabel = (lang?: string) => {
    const l = (lang || "").toLowerCase();
    if (l === "id") return "Bahasa Indonesia";
    if (l === "en") return "Bahasa Inggris";
    if (l === "mixed") return "Dwibahasa (ID/EN)";
    return (lang || "Unknown").toUpperCase();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[88vh] flex flex-col p-6 overflow-hidden">
        {/* Header */}
        <DialogHeader className="pb-2 border-b">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Sparkles className="h-4 w-4" />
                </span>
                <DialogTitle className="text-lg font-bold truncate">
                  Ringkasan Ekstraktif Dokumen
                </DialogTitle>
              </div>
              <DialogDescription className="text-xs text-muted-foreground line-clamp-1 font-medium">
                {documentTitle}
              </DialogDescription>
            </div>

            {documentType && (
              <Badge variant="outline" className="shrink-0 text-xs uppercase">
                {documentType}
              </Badge>
            )}
          </div>
        </DialogHeader>

        {/* Tabs */}
        <Tabs
          defaultValue="doc"
          value={activeTab}
          onValueChange={(val) => setActiveTab(val as "doc" | "query")}
          className="flex-1 flex flex-col min-h-0 mt-2"
        >
          <div className="flex items-center justify-between gap-2 pb-2">
            <TabsList className="grid grid-cols-2 w-[340px]">
              <TabsTrigger value="doc" className="text-xs flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5" />
                Intisari Dokumen
              </TabsTrigger>
              <TabsTrigger
                value="query"
                disabled={!activeQuery.trim()}
                className="text-xs flex items-center gap-1.5"
              >
                <Search className="h-3.5 w-3.5" />
                Relevansi Kueri
              </TabsTrigger>
            </TabsList>

            {/* Action buttons */}
            <div className="flex items-center gap-1.5">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 px-2 text-xs gap-1"
                onClick={() => {
                  if (activeTab === "doc") {
                    loadDocSummary(true);
                  } else {
                    loadQuerySummary(true);
                  }
                }}
                disabled={activeTab === "doc" ? docLoading : queryLoading}
                title="Komputasi ulang / perbarui ringkasan"
              >
                <RefreshCw
                  className={`h-3.5 w-3.5 ${
                    (activeTab === "doc" ? docLoading : queryLoading) ? "animate-spin" : ""
                  }`}
                />
                <span className="hidden sm:inline">Segarkan</span>
              </Button>

              <Button
                variant="outline"
                size="sm"
                className="h-8 px-2 text-xs gap-1"
                onClick={() => {
                  const currentSummary = activeTab === "doc" ? docSummary : querySummary;
                  if (currentSummary?.summary_text) {
                    handleCopy(currentSummary.summary_text);
                  }
                }}
                disabled={activeTab === "doc" ? !docSummary?.summary_text : !querySummary?.summary_text}
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-600" />
                    <span className="text-emerald-600">Tersalin</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    <span>Salin</span>
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* TAB 1: Dokumen Summary Content */}
          <TabsContent value="doc" className="flex-1 overflow-y-auto space-y-4 pr-1 mt-1">
            {docLoading ? (
              <div className="space-y-3 pt-2">
                <div className="flex gap-2 items-center">
                  <Skeleton className="h-5 w-24 rounded-full" />
                  <Skeleton className="h-5 w-32 rounded-full" />
                </div>
                <Skeleton className="h-24 w-full rounded-lg" />
                <Skeleton className="h-16 w-full rounded-lg" />
                <Skeleton className="h-16 w-full rounded-lg" />
              </div>
            ) : docError ? (
              <div className="p-4 rounded-lg bg-destructive/10 text-destructive flex items-start gap-3">
                <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold">Gagal Menghasilkan Ringkasan</p>
                  <p className="text-xs mt-1">{docError}</p>
                </div>
              </div>
            ) : docSummary ? (
              <div className="space-y-4">
                {/* Meta Badges */}
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <Badge variant="secondary" className="font-normal">
                    🌐 {formatLanguageLabel(docSummary.language)}
                  </Badge>
                  <Badge variant="outline" className="font-normal">
                    Algoritma: {docSummary.algorithm === "textrank_mmr" ? "TextRank + MMR" : docSummary.algorithm}
                  </Badge>
                  <span className="text-muted-foreground flex items-center gap-1 font-mono text-[11px] ml-auto">
                    {docSummary.cached ? (
                      <span className="inline-flex items-center text-emerald-600 dark:text-emerald-400 gap-0.5">
                        <Zap className="h-3 w-3" /> Cache ({docSummary.processing_time_ms.toFixed(1)} ms)
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-0.5">
                        <Clock className="h-3 w-3" /> {docSummary.processing_time_ms.toFixed(1)} ms
                      </span>
                    )}
                  </span>
                </div>

                {/* Key Sentences Breakdown with Page Badges */}
                {docSummary.key_sentences.length > 0 ? (
                  <div className="space-y-3">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                      Poin-Poin Utama Terpilih ({docSummary.key_sentences.length} Kalimat):
                    </p>

                    <div className="space-y-2.5">
                      {docSummary.key_sentences.map((item, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg border bg-card hover:bg-muted/30 transition-colors text-sm flex gap-3"
                        >
                          <span className="shrink-0 flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-primary font-mono text-xs font-semibold mt-0.5">
                            {idx + 1}
                          </span>
                          <div className="flex-1 space-y-1.5">
                            <p className="leading-relaxed text-foreground/90">{item.text}</p>
                            <div className="flex items-center gap-2 pt-0.5">
                              {item.page && (
                                <Badge
                                  variant="secondary"
                                  className="text-[11px] h-5 px-1.5 gap-1 bg-muted text-muted-foreground font-normal"
                                >
                                  <BookOpen className="h-3 w-3" />
                                  Halaman {item.page}
                                </Badge>
                              )}
                              <span className="text-[10px] text-muted-foreground font-mono">
                                Skor Centrality: {item.score.toFixed(3)}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <Separator />

                    {/* Unified Narrative Box */}
                    <div className="p-3.5 rounded-lg bg-muted/40 border border-muted space-y-1.5">
                      <p className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                        <FileText className="h-3.5 w-3.5 text-primary" />
                        Alur Ringkasan Utuh:
                      </p>
                      <p className="text-xs leading-relaxed text-muted-foreground italic">
                        &ldquo;{docSummary.summary_text}&rdquo;
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <p className="text-sm">{docSummary.summary_text}</p>
                  </div>
                )}
              </div>
            ) : null}
          </TabsContent>

          {/* TAB 2: Query-Focused Summary Content */}
          <TabsContent value="query" className="flex-1 overflow-y-auto space-y-4 pr-1 mt-1">
            {queryLoading ? (
              <div className="space-y-3 pt-2">
                <Skeleton className="h-6 w-48 rounded" />
                <Skeleton className="h-20 w-full rounded-lg" />
                <Skeleton className="h-20 w-full rounded-lg" />
              </div>
            ) : queryError ? (
              <div className="p-4 rounded-lg bg-destructive/10 text-destructive flex items-start gap-3">
                <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold">Gagal Menghasilkan Relevansi Kueri</p>
                  <p className="text-xs mt-1">{queryError}</p>
                </div>
              </div>
            ) : querySummary ? (
              <div className="space-y-4">
                {/* Query Header Callout */}
                <div className="p-3 rounded-lg bg-primary/5 border border-primary/20 flex items-center justify-between gap-2 text-xs">
                  <div>
                    <span className="text-muted-foreground font-medium">Fokus Kueri: </span>
                    <span className="font-semibold text-primary">&ldquo;{activeQuery}&rdquo;</span>
                  </div>
                  <span className="text-muted-foreground font-mono text-[11px] shrink-0">
                    {querySummary.cached ? (
                      <span className="text-emerald-600 dark:text-emerald-400">⚡ Cache</span>
                    ) : (
                      `${querySummary.processing_time_ms.toFixed(1)} ms`
                    )}
                  </span>
                </div>

                {/* Sentences */}
                {querySummary.key_sentences.length > 0 ? (
                  <div className="space-y-3">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                      Bukti Kalimat Terpaling Menjawab Kueri:
                    </p>

                    <div className="space-y-2.5">
                      {querySummary.key_sentences.map((item, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg border bg-card hover:bg-muted/30 transition-colors text-sm flex gap-3"
                        >
                          <span className="shrink-0 flex h-5 w-5 items-center justify-center rounded-full bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300 font-mono text-xs font-semibold mt-0.5">
                            {idx + 1}
                          </span>
                          <div className="flex-1 space-y-1.5">
                            <p className="leading-relaxed text-foreground/90">{item.text}</p>
                            <div className="flex items-center gap-2 pt-0.5">
                              {item.page && (
                                <Badge
                                  variant="secondary"
                                  className="text-[11px] h-5 px-1.5 gap-1 bg-muted text-muted-foreground font-normal"
                                >
                                  <BookOpen className="h-3 w-3" />
                                  Halaman {item.page}
                                </Badge>
                              )}
                              <span className="text-[10px] text-muted-foreground font-mono">
                                Kemiripan Semantik: {(item.score * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="p-6 text-center text-muted-foreground rounded-lg bg-muted/20 border">
                    <p className="text-sm font-medium">{querySummary.summary_text}</p>
                  </div>
                )}
              </div>
            ) : null}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
