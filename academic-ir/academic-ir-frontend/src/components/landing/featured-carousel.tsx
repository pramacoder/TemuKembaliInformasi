"use client";

import { useState } from "react";
import { FEATURED_DOCUMENTS } from "@/lib/curated-documents";
import { AcademicCover } from "@/components/covers/academic-cover";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Sparkles, ChevronLeft, ChevronRight, Layers } from "lucide-react";
import { type SearchResult } from "@/lib/api";
import { DocumentReaderDialog } from "@/components/document-reader-dialog";
import { SummaryDialog } from "@/components/summary-dialog";

interface FeaturedCarouselProps {
  onSearchTopic?: (query: string) => void;
}

export function FeaturedCarousel({ onSearchTopic }: FeaturedCarouselProps) {
  const [selectedDoc, setSelectedDoc] = useState<SearchResult | null>(null);
  const [readerDocId, setReaderDocId] = useState<string | null>(null);
  const [summaryDoc, setSummaryDoc] = useState<{ id: string; title: string; type: any } | null>(null);

  return (
    <section className="py-14 sm:py-20 bg-zinc-50/50 dark:bg-zinc-900/30 border-b border-zinc-200/80 dark:border-zinc-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header (Pinterest Ref 2 "Deciding What to Read Next?") */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-10 gap-4">
          <div>
            <p className="font-mono text-xs font-semibold uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
              Koleksi Unggulan &amp; Riset Terpilih
            </p>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-zinc-950 dark:text-zinc-50 tracking-tight mt-1">
              Rekomendasi Dokumen untuk Anda
            </h2>
          </div>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 max-w-sm">
            Kumpulan dokumen berbobot tinggi dengan indeks chunk lengkap, siap dibaca atau diringkas oleh AI.
          </p>
        </div>

        {/* Responsive Grid of Featured Documents with Minimalist Swiss Covers (Ref 2 & 4) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURED_DOCUMENTS.map((doc) => {
            const author = doc.authors.length > 0 ? doc.authors.join(", ") : doc.institution || "Academic IR";

            return (
              <div
                key={doc.id}
                className="group flex flex-col bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200/90 dark:border-zinc-800 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden"
              >
                {/* ── Top Cover Display Area with Subtle Ambient Matting ── */}
                <div className="p-6 bg-gradient-to-b from-zinc-100/60 via-zinc-50/40 to-transparent dark:from-zinc-800/40 dark:to-transparent flex justify-center items-center">
                  <div className="transform transition-transform duration-300 group-hover:scale-105">
                    <AcademicCover
                      documentId={doc.document_id}
                      documentType={doc.document_type}
                      title={doc.title}
                      authors={doc.authors}
                      year={doc.year}
                      institution={doc.institution}
                      course={doc.course}
                      size="md"
                    />
                  </div>
                </div>

                {/* ── Document Details ── */}
                <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <Badge
                        variant="secondary"
                        className="text-[10px] font-mono uppercase tracking-wider bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200"
                      >
                        {doc.source}
                      </Badge>

                      {doc.chunk_count && (
                        <span className="flex items-center gap-1 font-mono text-[10px] text-zinc-500">
                          <Layers className="h-3 w-3" />
                          {doc.chunk_count} Chunks
                        </span>
                      )}
                    </div>

                    <h3 className="text-sm font-bold text-zinc-900 dark:text-zinc-100 leading-snug line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {doc.title}
                    </h3>

                    <p className="text-xs text-zinc-500 dark:text-zinc-400 line-clamp-1">
                      {author}
                    </p>

                    <p className="text-xs text-zinc-600 dark:text-zinc-400 line-clamp-2 leading-relaxed pt-1">
                      {doc.abstract || doc.snippet}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="pt-3 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="default"
                      className="flex-1 h-8 text-xs gap-1.5 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-900 font-medium"
                      onClick={() => setReaderDocId(doc.document_id)}
                    >
                      <BookOpen className="h-3 w-3" />
                      Baca Dokumen
                    </Button>

                    <Button
                      size="sm"
                      variant="outline"
                      className="h-8 text-xs gap-1.5 text-zinc-700 dark:text-zinc-300 border-zinc-200 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800"
                      onClick={() =>
                        setSummaryDoc({
                          id: doc.document_id,
                          title: doc.title,
                          type: doc.document_type,
                        })
                      }
                    >
                      <Sparkles className="h-3 w-3 text-amber-500" />
                      Ringkasan
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Reader Dialog Modal */}
        {readerDocId && (
          <DocumentReaderDialog
            isOpen={true}
            onClose={() => setReaderDocId(null)}
            documentId={readerDocId}
            initialPage={1}
            activeQuery=""
            onOpenSummary={() => {
              const d = FEATURED_DOCUMENTS.find((x) => x.document_id === readerDocId);
              if (d) {
                setReaderDocId(null);
                setSummaryDoc({
                  id: d.document_id,
                  title: d.title,
                  type: d.document_type,
                });
              }
            }}
          />
        )}

        {/* Summary Dialog Modal */}
        {summaryDoc && (
          <SummaryDialog
            isOpen={true}
            onClose={() => setSummaryDoc(null)}
            documentId={summaryDoc.id}
            documentTitle={summaryDoc.title}
            activeQuery=""
            documentType={summaryDoc.type}
          />
        )}

      </div>
    </section>
  );
}
