"use client";

import { useState } from "react";
import { Search, Sparkles, BookOpen, Layers, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AcademicCover } from "@/components/covers/academic-cover";
import { type DocumentType } from "@/lib/api";

interface HeroSectionProps {
  onSearch: (query: string, documentType?: DocumentType | null) => void;
  query: string;
  onQueryChange: (query: string) => void;
}

const QUICK_TAGS = [
  { label: "Machine Learning", query: "Machine Learning" },
  { label: "Vector Space Model", query: "Vector Space Model TF-IDF" },
  { label: "Sentence-BERT", query: "Sentence-BERT" },
  { label: "Manajemen Proyek TI", query: "Manajemen Proyek TI" },
  { label: "State Machine", query: "Behavioral State Machine" },
  { label: "Cosine Similarity", query: "Cosine Similarity Ranking" },
];

export function HeroSection({
  onSearch,
  query,
  onQueryChange,
}: HeroSectionProps) {
  const [selectedType, setSelectedType] = useState<DocumentType | "ALL">("ALL");

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    onSearch(query.trim(), selectedType === "ALL" ? null : selectedType);
  };

  const handleTagClick = (tagQuery: string) => {
    onQueryChange(tagQuery);
    onSearch(tagQuery, selectedType === "ALL" ? null : selectedType);
  };

  return (
    <section className="relative overflow-hidden pt-8 pb-16 lg:pt-14 lg:pb-24 border-b border-zinc-200/80 dark:border-zinc-800 bg-gradient-to-b from-zinc-50/50 via-white to-zinc-50/30 dark:from-zinc-950 dark:via-zinc-900/40 dark:to-zinc-950">
      {/* ── Architectural Blueprint Background Grid (Pinterest Ref 1) ── */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.035] dark:opacity-[0.06]"
        style={{
          backgroundImage:
            "linear-gradient(to right, #000 1px, transparent 1px), linear-gradient(to bottom, #000 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* Subtle architectural arched glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 max-w-4xl h-80 bg-gradient-to-b from-blue-100/20 via-indigo-50/10 to-transparent blur-3xl pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-8 items-center">
          
          {/* ── Left Column: Editorial Headline & Search Box ── */}
          <div className="lg:col-span-7 space-y-6 text-left">
            {/* Top pill badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200/90 dark:border-zinc-700/80 text-xs font-medium text-zinc-700 dark:text-zinc-300">
              <span className="flex h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
              <span>Multi-Corpus IR System</span>
              <span className="text-zinc-300 dark:text-zinc-600">|</span>
              <span className="font-mono text-zinc-500 dark:text-zinc-400">56,881 Chunks Terindeks</span>
            </div>

            {/* Main Editorial Headline (Pinterest Ref 2 style) */}
            <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-zinc-950 dark:text-white leading-[1.12]">
              Temukan &amp; Telusuri{" "}
              <span className="relative inline-block text-zinc-900 dark:text-zinc-100 underline decoration-zinc-300 dark:decoration-zinc-700 decoration-wavy decoration-1 underline-offset-8">
                Pengetahuan Ilmiah
              </span>{" "}
              dalam Hitungan Detik.
            </h1>

            <p className="text-base sm:text-lg text-zinc-600 dark:text-zinc-400 max-w-2xl leading-relaxed">
              Sistem Information Retrieval akademik multi-korpus berbasis{" "}
              <strong className="text-zinc-800 dark:text-zinc-200 font-semibold">TF-IDF Vector Space Model &amp; BM25</strong>. 
              Mencari secara cerdas hingga ke potongan paragraf, nomor halaman, dan ringkasan intisari.
            </p>

            {/* ── Search Bar Component (Pinterest Ref 1 & 2 Synthesis) ── */}
            <form
              onSubmit={handleSubmit}
              className="p-1.5 sm:p-2 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-xl shadow-zinc-900/5 transition-all duration-200 focus-within:ring-2 focus-within:ring-zinc-900 dark:focus-within:ring-zinc-400"
            >
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                {/* Corpus Selector Dropdown */}
                <div className="sm:border-r border-zinc-200 dark:border-zinc-800 pr-2">
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value as DocumentType | "ALL")}
                    className="w-full sm:w-auto bg-transparent px-3 py-2 text-xs font-semibold text-zinc-700 dark:text-zinc-300 rounded-lg focus:outline-none cursor-pointer"
                  >
                    <option value="ALL">Semua Korpus</option>
                    <option value="MATERIAL">Bahan Kuliah (OCW)</option>
                    <option value="RESEARCH">Riset Ilmiah (arXiv/CORE)</option>
                    <option value="THESIS">Skripsi &amp; Tesis</option>
                  </select>
                </div>

                {/* Main Input Text */}
                <div className="flex-1 flex items-center gap-2.5 px-3 min-w-0">
                  <Search className="h-4 w-4 text-zinc-400 shrink-0" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => onQueryChange(e.target.value)}
                    placeholder="Ketik topik, judul jurnal, istilah teknis, atau materi kuliah..."
                    className="w-full bg-transparent text-sm text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none py-1.5"
                  />
                </div>

                {/* Submit Action Button */}
                <Button
                  type="submit"
                  size="default"
                  className="h-10 sm:h-11 px-6 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-white dark:text-zinc-900 font-medium text-sm gap-2 shrink-0 shadow-md"
                >
                  <span>Cari</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            </form>

            {/* ── Quick Search Tag Pills (Pinterest Ref 3) ── */}
            <div className="space-y-2 pt-1">
              <div className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
                <Sparkles className="h-3.5 w-3.5 text-amber-500 shrink-0" />
                <span className="font-medium">Pencarian Populer:</span>
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                {QUICK_TAGS.map((tag) => (
                  <button
                    key={tag.label}
                    type="button"
                    onClick={() => handleTagClick(tag.query)}
                    className="text-xs px-2.5 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800/60 hover:bg-zinc-200/80 dark:hover:bg-zinc-700/80 text-zinc-700 dark:text-zinc-300 border border-zinc-200/80 dark:border-zinc-700/60 transition-colors"
                  >
                    {tag.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick trust metrics */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-zinc-200/60 dark:border-zinc-800/60 text-xs">
              <div>
                <p className="font-mono text-lg font-bold text-zinc-900 dark:text-zinc-100">263</p>
                <p className="text-zinc-500 dark:text-zinc-400">Dokumen Penuh</p>
              </div>
              <div>
                <p className="font-mono text-lg font-bold text-zinc-900 dark:text-zinc-100">9,748</p>
                <p className="text-zinc-500 dark:text-zinc-400">Chunk Paragraf</p>
              </div>
              <div>
                <p className="font-mono text-lg font-bold text-zinc-900 dark:text-zinc-100">100%</p>
                <p className="text-zinc-500 dark:text-zinc-400">Tolerant Typo</p>
              </div>
            </div>
          </div>

          {/* ── Right Column: 3D Floating Perspective Book Cover Showcase (Pinterest Ref 2 & 4) ── */}
          <div className="lg:col-span-5 flex justify-center items-center py-6">
            <div className="relative w-full max-w-[340px] sm:max-w-[400px] h-[340px] flex items-center justify-center">
              
              {/* Background ambient halo */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-zinc-200/50 via-slate-100/40 to-transparent dark:from-zinc-800/40 dark:to-transparent blur-2xl" />

              {/* Cover 1 (Left Wing - Angled) */}
              <div
                className="absolute left-2 sm:left-4 z-10 transition-transform duration-300 hover:z-30 hover:scale-105"
                style={{
                  transform: "rotate(-8deg) translateY(12px) scale(0.9)",
                }}
              >
                <AcademicCover
                  documentId="MAT-000008"
                  documentType="MATERIAL"
                  title="Slide 01 - Introduction to Project Management"
                  institution="Universitas Indonesia"
                  course="Manajemen Proyek TI"
                  size="md"
                  year={2023}
                />
              </div>

              {/* Cover 2 (Center Hero - Elevated) */}
              <div
                className="relative z-20 transition-transform duration-300 hover:scale-105"
                style={{
                  transform: "translateY(-10px)",
                }}
              >
                <AcademicCover
                  documentId="RES-000006"
                  documentType="RESEARCH"
                  title="Sentence-BERT: Sentence Embeddings using Siamese BERT"
                  authors={["Nils Reimers", "Iryna Gurevych"]}
                  institution="arXiv cs.CL"
                  size="md"
                  year={2019}
                />
              </div>

              {/* Cover 3 (Right Wing - Angled) */}
              <div
                className="absolute right-2 sm:right-4 z-10 transition-transform duration-300 hover:z-30 hover:scale-105"
                style={{
                  transform: "rotate(8deg) translateY(16px) scale(0.9)",
                }}
              >
                <AcademicCover
                  documentId="THS-000004"
                  documentType="THESIS"
                  title="Evaluasi Temu Kembali Informasi & Kemiripan Dokumen"
                  authors={["Ahmad Fauzi"]}
                  institution="Universitas Indonesia"
                  course="Skripsi Sarjana"
                  size="md"
                  year={2023}
                />
              </div>

            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
