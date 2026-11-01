"use client";

import {
  BrainCircuit,
  Search,
  Sparkles,
  Kanban,
  Code2,
  Cpu,
  GraduationCap,
  Database,
  ArrowUpRight,
} from "lucide-react";
import { FEATURED_CATEGORIES, type FeaturedCategory } from "@/lib/curated-documents";

interface CategoryGridProps {
  onSelectCategory: (query: string) => void;
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  BrainCircuit,
  Search,
  Sparkles,
  Kanban,
  Code2,
  Cpu,
  GraduationCap,
  Database,
};

export function CategoryGrid({ onSelectCategory }: CategoryGridProps) {
  return (
    <section className="py-14 sm:py-20 border-b border-zinc-200/80 dark:border-zinc-800 bg-white dark:bg-zinc-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-10 gap-4">
          <div>
            <p className="font-mono text-xs font-semibold uppercase tracking-widest text-zinc-500 dark:text-zinc-400">
              Kategori Terindeks
            </p>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-zinc-950 dark:text-zinc-50 tracking-tight mt-1">
              Eksplorasi Berdasarkan Disiplin Ilmu
            </h2>
          </div>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 max-w-sm">
            Jelajahi dokumen berdasarkan taksonomi keilmuan yang telah terkelompokkan dalam basis data kami.
          </p>
        </div>

        {/* 2x4 Categories Grid (Pinterest Ref 2 Style) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURED_CATEGORIES.map((cat: FeaturedCategory) => {
            const Icon = ICON_MAP[cat.iconName] || Search;

            return (
              <div
                key={cat.id}
                onClick={() => onSelectCategory(cat.query)}
                className="group relative p-5 rounded-2xl bg-zinc-50/60 dark:bg-zinc-900/50 border border-zinc-200/80 dark:border-zinc-800/80 hover:bg-white dark:hover:bg-zinc-900 hover:border-zinc-300 dark:hover:border-zinc-700 hover:shadow-lg transition-all duration-200 cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="h-10 w-10 rounded-xl bg-white dark:bg-zinc-800 border border-zinc-200/80 dark:border-zinc-700/80 flex items-center justify-center text-zinc-800 dark:text-zinc-200 group-hover:bg-zinc-900 group-hover:text-white dark:group-hover:bg-zinc-100 dark:group-hover:text-zinc-900 transition-colors">
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="font-mono text-[11px] text-zinc-500 dark:text-zinc-400 bg-white dark:bg-zinc-800 px-2 py-0.5 rounded-full border border-zinc-200/60 dark:border-zinc-700/60">
                      {cat.documentCount} Dokumen
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-zinc-900 dark:text-zinc-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {cat.name}
                  </h3>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 leading-relaxed line-clamp-2">
                    {cat.description}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-zinc-200/60 dark:border-zinc-800/60 flex items-center justify-between text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                  <span>Lihat Dokumen</span>
                  <ArrowUpRight className="h-3.5 w-3.5 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
