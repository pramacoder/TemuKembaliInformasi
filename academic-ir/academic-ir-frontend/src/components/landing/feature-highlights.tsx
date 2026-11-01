"use client";

import { Layers, Sparkles, ShieldCheck, ArrowRight } from "lucide-react";

export function FeatureHighlights() {
  const features = [
    {
      icon: Layers,
      title: "Chunk-Level Retrieval",
      badge: "TF-IDF + VSM",
      desc: "Algoritma memecah ribuan halaman PDF menjadi 9,700+ potongan paragraf bermakna. Sistem memetakan kecocokan hingga ke nomor halaman persis dengan skor kemiripan Cosine Similarity.",
    },
    {
      icon: Sparkles,
      title: "AI Extractive Summarization",
      badge: "TextRank & SVD",
      desc: "Menghasilkan intisari otomatis baik ringkasan tingkat dokumen utuh maupun ringkasan terfokus pada pertanyaan spesifik Anda tanpa memerlukan koneksi ke API eksternal yang lambat.",
    },
    {
      icon: ShieldCheck,
      title: "Tolerant Retrieval Layer",
      badge: "BM25 Lexical",
      desc: "Mendeteksi salah ketik (typo), singkatan umum akademik, serta bentuk kata baku bahasa Indonesia & Inggris secara otomatis dengan fallback cerdas berbasis n-gram.",
    },
  ];

  return (
    <section className="py-16 sm:py-24 bg-zinc-50/60 dark:bg-zinc-900/40 border-b border-zinc-200/80 dark:border-zinc-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="text-center max-w-2xl mx-auto mb-14">
          <p className="font-mono text-xs font-semibold uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
            Arsitektur Mesin Pencari
          </p>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-zinc-950 dark:text-zinc-50 tracking-tight mt-1">
            Dirancang untuk Presisi Akademik Tinggi
          </h2>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-2">
            Menggabungkan keandalan Vector Space Model klasik dengan antarmuka web modern yang responsif.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((feat) => {
            const Icon = feat.icon;
            return (
              <div
                key={feat.title}
                className="p-6 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-sm flex flex-col justify-between hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="h-10 w-10 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-zinc-800 dark:text-zinc-200">
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="font-mono text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
                      {feat.badge}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-zinc-900 dark:text-zinc-100">
                    {feat.title}
                  </h3>
                  <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-2 leading-relaxed">
                    {feat.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
