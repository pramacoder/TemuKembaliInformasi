"use client";

import { useEffect, useState, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  fetchDocumentPages,
  type DocumentPagesResponse,
  type DocumentPageItem,
  DOCUMENT_TYPE_COLORS,
  DOCUMENT_TYPE_LABELS,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Copy,
  Check,
  FileText,
  Search,
  Users,
  Calendar,
  Layers,
  ZoomIn,
  ZoomOut,
  Sparkles,
} from "lucide-react";

interface DocumentReaderDialogProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: string;
  initialPage?: number;
  activeQuery?: string;
  onOpenSummary?: () => void;
}

export function DocumentReaderDialog({
  isOpen,
  onClose,
  documentId,
  initialPage = 1,
  activeQuery = "",
  onOpenSummary,
}: DocumentReaderDialogProps) {
  const [data, setData] = useState<DocumentPagesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [viewMode, setViewMode] = useState<"single" | "continuous">("single");
  const [fontSize, setFontSize] = useState<"sm" | "base" | "lg">("base");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isOpen || !documentId) return;

    setLoading(true);
    setError(null);
    fetchDocumentPages(documentId, activeQuery)
      .then((res) => {
        setData(res);
        // Find page matching initialPage
        if (res.pages.length > 0) {
          const targetIdx = res.pages.findIndex(
            (p) => p.page_number === initialPage
          );
          setCurrentPageIndex(targetIdx >= 0 ? targetIdx : 0);
        }
      })
      .catch((err) => {
        setError(err?.message ?? "Gagal memuat dokumen");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [isOpen, documentId, initialPage]);

  // Query tokens for highlighting
  const queryTokens = useMemo(() => {
    if (!activeQuery.trim()) return [];
    return activeQuery
      .toLowerCase()
      .split(/\s+/)
      .filter((t) => t.length > 2);
  }, [activeQuery]);

  const highlightText = (text: string) => {
    if (!queryTokens.length || !text) return text;
    // Build regex to match any of the query terms
    const escaped = queryTokens.map((t) =>
      t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
    );
    const regex = new RegExp(`(${escaped.join("|")})`, "gi");
    const parts = text.split(regex);

    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark
          key={i}
          className="bg-amber-200 dark:bg-amber-900/60 text-amber-950 dark:text-amber-100 rounded px-1 font-medium"
        >
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  const currentPage = data?.pages[currentPageIndex];

  const handleCopy = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const fontSizeClass =
    fontSize === "sm"
      ? "text-xs leading-relaxed"
      : fontSize === "lg"
      ? "text-base leading-loose"
      : "text-sm leading-relaxed";

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[92vh] flex flex-col p-6 overflow-hidden">
        {/* Header */}
        <DialogHeader className="pb-3 border-b">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1.5 min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <BookOpen className="h-4 w-4" />
                </span>
                <DialogTitle className="text-base sm:text-lg font-bold line-clamp-1">
                  {data?.title ?? "Membaca Dokumen Lengkap"}
                </DialogTitle>
                {data?.document_type && (
                  <Badge
                    className={cn(
                      "text-xs font-medium border-0",
                      DOCUMENT_TYPE_COLORS[data.document_type]
                    )}
                  >
                    {DOCUMENT_TYPE_LABELS[data.document_type]}
                  </Badge>
                )}
              </div>

              {/* Document metadata row */}
              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                {data?.authors && data.authors.length > 0 && (
                  <span className="flex items-center gap-1 truncate max-w-[240px]">
                    <Users className="h-3 w-3 shrink-0" />
                    {data.authors.join(", ")}
                  </span>
                )}
                {data?.year && (
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {data.year}
                  </span>
                )}
                {data?.total_pages && (
                  <span className="flex items-center gap-1 font-medium text-foreground">
                    <Layers className="h-3 w-3" />
                    {data.total_pages} Halaman Fisik
                  </span>
                )}
              </div>
            </div>

            {/* Top Right Quick Actions */}
            <div className="flex items-center gap-1.5 shrink-0">
              {onOpenSummary && (
                <Button
                  size="sm"
                  variant="outline"
                  className="h-8 text-xs gap-1 border-primary/30 text-primary hover:bg-primary/10"
                  onClick={onOpenSummary}
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Ringkasan</span>
                </Button>
              )}
              {data?.source_url && (
                <Button
                  size="sm"
                  variant="outline"
                  className="h-8 text-xs gap-1"
                  onClick={() => window.open(data.source_url!, "_blank")}
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Unduh PDF</span>
                </Button>
              )}
            </div>
          </div>

          {/* Matched Pages Quick-Jump Bar */}
          {data?.matched_pages && data.matched_pages.length > 0 && (
            <div className="flex items-center gap-2 pt-2 text-xs flex-wrap">
              <span className="text-muted-foreground flex items-center gap-1 font-medium shrink-0">
                <Search className="h-3 w-3 text-amber-500" />
                Halaman Cocok Kueri:
              </span>
              <div className="flex items-center gap-1 flex-wrap">
                {data.matched_pages.map((pNum) => {
                  const pIdx = data.pages.findIndex(
                    (p) => p.page_number === pNum
                  );
                  const isCurrent = currentPage?.page_number === pNum;
                  return (
                    <Button
                      key={pNum}
                      size="sm"
                      variant={isCurrent ? "default" : "secondary"}
                      className={cn(
                        "h-6 px-2 text-[11px] font-mono",
                        isCurrent
                          ? "bg-amber-600 hover:bg-amber-700 text-white"
                          : "bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 dark:bg-amber-950/40 dark:text-amber-200 dark:border-amber-800"
                      )}
                      onClick={() => {
                        if (pIdx >= 0) setCurrentPageIndex(pIdx);
                      }}
                    >
                      Hal. {pNum}
                    </Button>
                  );
                })}
              </div>
            </div>
          )}
        </DialogHeader>

        {/* Toolbar & Page Navigation */}
        <div className="flex items-center justify-between gap-2 py-2 border-b text-xs">
          <div className="flex items-center gap-1.5">
            {viewMode === "single" && data?.pages && data.pages.length > 1 && (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 px-2 gap-1"
                  disabled={currentPageIndex <= 0}
                  onClick={() => setCurrentPageIndex((prev) => prev - 1)}
                >
                  <ChevronLeft className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Sebelumnya</span>
                </Button>

                <span className="font-mono font-medium px-2 py-1 bg-muted rounded">
                  Hal. {currentPage?.page_number ?? 1} / {data.total_pages}
                </span>

                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 px-2 gap-1"
                  disabled={currentPageIndex >= data.pages.length - 1}
                  onClick={() => setCurrentPageIndex((prev) => prev + 1)}
                >
                  <span className="hidden sm:inline">Berikutnya</span>
                  <ChevronRight className="h-3.5 w-3.5" />
                </Button>
              </>
            )}

            <Button
              size="sm"
              variant="ghost"
              className="h-7 px-2 text-xs"
              onClick={() =>
                setViewMode((prev) => (prev === "single" ? "continuous" : "single"))
              }
            >
              {viewMode === "single" ? "Tampilkan Semua Halaman" : "Mode Halaman Tunggal"}
            </Button>
          </div>

          {/* Right Toolbar: Font Size & Copy */}
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant="ghost"
              className="h-7 w-7 p-0"
              title="Perkecil Teks"
              onClick={() =>
                setFontSize((prev) => (prev === "lg" ? "base" : "sm"))
              }
            >
              <ZoomOut className="h-3.5 w-3.5" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              className="h-7 w-7 p-0"
              title="Perbesar Teks"
              onClick={() =>
                setFontSize((prev) => (prev === "sm" ? "base" : "lg"))
              }
            >
              <ZoomIn className="h-3.5 w-3.5" />
            </Button>

            <Button
              size="sm"
              variant="outline"
              className="h-7 px-2 text-xs gap-1 ml-1"
              onClick={() => {
                const textToCopy =
                  viewMode === "single"
                    ? currentPage?.text ?? ""
                    : data?.pages.map((p) => `--- Halaman ${p.page_number} ---\n${p.text}`).join("\n\n") ?? "";
                handleCopy(textToCopy);
              }}
            >
              {copied ? (
                <>
                  <Check className="h-3 w-3 text-emerald-600" />
                  <span className="text-emerald-600">Tersalin</span>
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3" />
                  <span>Salin Teks</span>
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Document Content View */}
        <div className="flex-1 overflow-y-auto pr-2 py-3 space-y-4">
          {loading ? (
            <div className="space-y-4 py-4">
              <Skeleton className="h-20 w-full rounded-lg" />
              <Skeleton className="h-32 w-full rounded-lg" />
              <Skeleton className="h-48 w-full rounded-lg" />
            </div>
          ) : error ? (
            <div className="p-6 text-center text-destructive">
              <p className="font-semibold text-sm">{error}</p>
            </div>
          ) : data ? (
            <>
              {/* Optional Abstract banner on top if available */}
              {data.abstract && (
                <div className="p-4 rounded-lg bg-primary/5 border border-primary/20 space-y-1.5 mb-3">
                  <div className="flex items-center gap-1.5 font-semibold text-xs text-primary">
                    <FileText className="h-3.5 w-3.5" />
                    Abstrak Resmi Dokumen:
                  </div>
                  <p className="text-xs sm:text-sm leading-relaxed text-foreground/90 font-serif">
                    {highlightText(data.abstract)}
                  </p>
                </div>
              )}

              {/* Single Page View */}
              {viewMode === "single" && currentPage ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs text-muted-foreground pb-1">
                    <span className="font-semibold">
                      Halaman {currentPage.page_number} dari {data.total_pages}
                    </span>
                    <span>{currentPage.word_count} kata</span>
                  </div>

                  <div
                    className={cn(
                      "p-5 rounded-lg border bg-card shadow-sm font-serif text-foreground/90 whitespace-pre-wrap select-text",
                      fontSizeClass
                    )}
                  >
                    {highlightText(currentPage.text)}
                  </div>
                </div>
              ) : null}

              {/* Continuous All Pages View */}
              {viewMode === "continuous" && (
                <div className="space-y-6">
                  {data.pages.map((page) => (
                    <div
                      key={page.page_number}
                      id={`page-${page.page_number}`}
                      className="space-y-2"
                    >
                      <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
                        <span className="font-semibold text-primary flex items-center gap-1">
                          <BookOpen className="h-3 w-3" />
                          Halaman {page.page_number}
                          {page.has_match && (
                            <Badge
                              variant="secondary"
                              className="text-[10px] bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200 ml-1"
                            >
                              Cocok Kueri
                            </Badge>
                          )}
                        </span>
                        <span>{page.word_count} kata</span>
                      </div>

                      <div
                        className={cn(
                          "p-5 rounded-lg border bg-card shadow-sm font-serif text-foreground/90 whitespace-pre-wrap select-text",
                          fontSizeClass
                        )}
                      >
                        {highlightText(page.text)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
