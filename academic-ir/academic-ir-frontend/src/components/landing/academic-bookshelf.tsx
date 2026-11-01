"use client";

import { useState } from "react";
import { CoverSpine } from "@/components/covers/cover-spine";
import { FEATURED_DOCUMENTS } from "@/lib/curated-documents";
import { DocumentReaderDialog } from "@/components/document-reader-dialog";
import { SummaryDialog } from "@/components/summary-dialog";
import { Library, Sparkles, BookOpen } from "lucide-react";

export function AcademicBookshelf() {
  const [activeDocId, setActiveDocId] = useState<string | null>(null);
  const [summaryDoc, setSummaryDoc] = useState<{ id: string; title: string; type: any } | null>(null);

  const activeDoc = FEATURED_DOCUMENTS.find((d) => d.document_id === activeDocId);

  const spineSchemes = ["obsidian", "navy", "amber", "charcoal", "sage", "navy"] as const;

  return (
    <section className="py-16 sm:py-24 bg-white dark:bg-zinc-950 border-b border-zinc-200/80 dark:border-zinc-800 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header (Pinterest Ref 3) */}
        <div className="text-center max-w-2xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800 text-xs font-semibold text-zinc-700 dark:text-zinc-300 mb-3">
            <Library className="h-3.5 w-3.5 text-zinc-600 dark:text-zinc-400" />
            <span>Interactive Shelf Experience</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-zinc-950 dark:text-zinc-50 tracking-tight">
            Rak Dokumen Akademik Fisik
          </h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-2">
            Arahkan kursor atau sentuh punggung buku untuk menarik volume keluar dari rak dan membuka pembaca dokumen digital.
          </p>
        </div>

        {/* ── Visual Bookshelf Container ── */}
        <div className="relative pt-12 pb-6 max-w-4xl mx-auto flex flex-col items-center">
          
          {/* Books Row */}
          <div className="relative z-10 flex items-end justify-center gap-2 sm:gap-4 px-4 overflow-x-auto w-full pb-0.5">
            {FEATURED_DOCUMENTS.map((doc, idx) => (
              <CoverSpine
                key={doc.id}
                documentId={doc.document_id}
                title={doc.title}
                year={doc.year}
                documentType={doc.document_type}
                institution={doc.institution}
                colorScheme={spineSchemes[idx % spineSchemes.length]}
                onClick={() => setActiveDocId(doc.document_id)}
              />
            ))}
          </div>

          {/* ── Realistic Wooden / Slate Shelf Bar ── */}
          <div className="relative w-full z-20">
            {/* Top surface of shelf */}
            <div className="h-4 w-full bg-gradient-to-r from-zinc-800 via-zinc-700 to-zinc-800 rounded-t-xs shadow-md border-t border-zinc-600" />
            {/* Front thickness bevel */}
            <div className="h-6 w-full bg-gradient-to-b from-zinc-900 via-zinc-950 to-black rounded-b-md shadow-2xl flex items-center justify-between px-6">
              <span className="font-mono text-[9px] uppercase tracking-widest text-zinc-500">
                SHELF 01 — MULTI-CORPUS REPOSITORY
              </span>
              <span className="font-mono text-[9px] uppercase tracking-widest text-zinc-500">
                ACADEMIC IR
              </span>
            </div>
            {/* Shadow cast beneath the shelf */}
            <div className="h-6 w-full bg-gradient-to-b from-black/30 to-transparent blur-md" />
          </div>

        </div>

      </div>

      {/* Reader Dialog Modal */}
      {activeDocId && (
        <DocumentReaderDialog
          isOpen={true}
          onClose={() => setActiveDocId(null)}
          documentId={activeDocId}
          initialPage={1}
          activeQuery=""
          onOpenSummary={() => {
            if (activeDoc) {
              setActiveDocId(null);
              setSummaryDoc({
                id: activeDoc.document_id,
                title: activeDoc.title,
                type: activeDoc.document_type,
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
    </section>
  );
}
