"use client";

import { Building2, Globe2, BookOpenCheck, Library, GraduationCap } from "lucide-react";

const SOURCES = [
  {
    name: "OCW Universitas Indonesia",
    tag: "248 Bahan Kuliah",
    icon: GraduationCap,
    desc: "Slide & Materi Resmi Fasilkom UI",
  },
  {
    name: "arXiv.org Archive",
    tag: "High-Citation Papers",
    icon: Globe2,
    desc: "Komputasi & Information Retrieval",
  },
  {
    name: "CORE Open Access",
    tag: "Global Research",
    icon: Building2,
    desc: "Koleksi Jurnal Internasional",
  },
  {
    name: "DOAJ Index",
    tag: "Peer-Reviewed",
    icon: BookOpenCheck,
    desc: "Direktori Jurnal Akses Terbuka",
  },
  {
    name: "Institutional Repository",
    tag: "Skripsi & Tesis",
    icon: Library,
    desc: "Penelitian Tugas Akhir Terverifikasi",
  },
];

export function ProvenanceBar() {
  return (
    <section className="py-8 bg-zinc-50/80 dark:bg-zinc-900/40 border-b border-zinc-200/80 dark:border-zinc-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p className="text-center font-mono text-[10px] sm:text-xs font-semibold uppercase tracking-widest text-zinc-500 dark:text-zinc-400 mb-6">
          Terhubung Langsung ke Korpus Akademik Terverifikasi
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {SOURCES.map((source) => {
            const Icon = source.icon;
            return (
              <div
                key={source.name}
                className="flex items-center gap-3 p-3 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 shadow-xs hover:border-zinc-300 dark:hover:border-zinc-700 transition-colors"
              >
                <div className="h-9 w-9 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-zinc-700 dark:text-zinc-300 shrink-0">
                  <Icon className="h-4.5 w-4.5" />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold text-zinc-900 dark:text-zinc-100 truncate">
                    {source.name}
                  </p>
                  <p className="text-[10px] text-zinc-500 dark:text-zinc-400 truncate">
                    {source.tag}
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
