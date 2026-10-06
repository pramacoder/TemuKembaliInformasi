"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  type DocumentType,
  type RetrievalMode,
  type AggregationStrategy,
  DOCUMENT_TYPE_LABELS,
} from "@/lib/api";
import { Cpu, Filter, Layers, RotateCcw } from "lucide-react";

interface FilterSidebarProps {
  selectedType: DocumentType | null;
  yearFrom: string;
  yearTo: string;
  language: string;
  retrievalMode: RetrievalMode;
  aggregationStrategy: AggregationStrategy;
  onTypeChange: (type: DocumentType | null) => void;
  onYearFromChange: (value: string) => void;
  onYearToChange: (value: string) => void;
  onLanguageChange: (value: string) => void;
  onRetrievalModeChange: (mode: RetrievalMode) => void;
  onAggregationStrategyChange: (strategy: AggregationStrategy) => void;
  onReset: () => void;
  totalResults: number;
}

const ALL_TYPES: DocumentType[] = ["MATERIAL", "RESEARCH", "THESIS"];

export function FilterSidebar({
  selectedType,
  yearFrom,
  yearTo,
  language,
  retrievalMode,
  aggregationStrategy,
  onTypeChange,
  onYearFromChange,
  onYearToChange,
  onLanguageChange,
  onRetrievalModeChange,
  onAggregationStrategyChange,
  onReset,
  totalResults,
}: FilterSidebarProps) {
  return (
    <aside className="w-60 shrink-0 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-semibold">Filter & Model</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onReset}
          className="h-7 text-xs gap-1.5 text-muted-foreground hover:text-foreground"
        >
          <RotateCcw className="h-3 w-3" />
          Reset
        </Button>
      </div>

      <div className="text-xs text-muted-foreground">
        {totalResults} dokumen ditemukan
      </div>

      <Separator />

      {/* Model Retrieval Selection (TF-IDF vs BM25) */}
      <div className="space-y-3">
        <div className="flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5 text-primary" />
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Model Retrieval
          </p>
        </div>
        <div className="space-y-2">
          {[
            { id: "tfidf", label: "TF-IDF (Baseline A)", desc: "Vector Space Model" },
            { id: "bm25", label: "BM25 (Baseline B)", desc: "Okapi BM25" },
          ].map((m) => (
            <div
              key={m.id}
              onClick={() => onRetrievalModeChange(m.id as RetrievalMode)}
              className={`p-2 rounded-md border text-xs cursor-pointer transition-all ${
                retrievalMode === m.id
                  ? "border-primary bg-primary/10 font-medium text-foreground"
                  : "border-border hover:bg-muted/50 text-muted-foreground"
              }`}
            >
              <div className="font-semibold">{m.label}</div>
              <div className="text-[11px] text-muted-foreground">{m.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Aggregation Strategy */}
      <div className="space-y-3">
        <div className="flex items-center gap-1.5">
          <Layers className="h-3.5 w-3.5 text-primary" />
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Agregasi Dokumen
          </p>
        </div>
        <div className="space-y-1.5">
          {[
            { id: "max+2nd", label: "Max + 2nd Chunk (Default)", desc: "Seimbang diversitas" },
            { id: "max", label: "Max Chunk", desc: "Skor chunk tertinggi" },
            { id: "topN_avg", label: "Top-3 Average", desc: "Rata-rata 3 chunk" },
          ].map((strat) => (
            <div
              key={strat.id}
              onClick={() => onAggregationStrategyChange(strat.id as AggregationStrategy)}
              className={`p-1.5 px-2 rounded border text-xs cursor-pointer transition-all ${
                aggregationStrategy === strat.id
                  ? "border-primary bg-primary/10 font-medium text-foreground"
                  : "border-border hover:bg-muted/50 text-muted-foreground"
              }`}
            >
              <div className="font-medium">{strat.label}</div>
              <div className="text-[10px] text-muted-foreground">{strat.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Document Type */}
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Jenis Dokumen
        </p>
        <div className="space-y-2">
          <div className="flex items-center gap-2.5">
            <Checkbox
              id="type-all"
              checked={selectedType === null}
              onCheckedChange={() => onTypeChange(null)}
            />
            <Label htmlFor="type-all" className="text-sm cursor-pointer leading-none">
              Semua Jenis
            </Label>
          </div>
          {ALL_TYPES.map((type) => (
            <div key={type} className="flex items-center gap-2.5">
              <Checkbox
                id={`type-${type}`}
                checked={selectedType === type}
                onCheckedChange={(checked) => onTypeChange(checked ? type : null)}
              />
              <Label
                htmlFor={`type-${type}`}
                className="text-sm cursor-pointer leading-none"
              >
                {DOCUMENT_TYPE_LABELS[type]}
              </Label>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Language */}
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Bahasa
        </p>
        <div className="space-y-2">
          {[
            { value: "", label: "Semua Bahasa" },
            { value: "en", label: "English" },
            { value: "id", label: "Bahasa Indonesia" },
          ].map(({ value, label }) => (
            <div key={value} className="flex items-center gap-2.5">
              <Checkbox
                id={`lang-${value || "all"}`}
                checked={language === value}
                onCheckedChange={() => onLanguageChange(value)}
              />
              <Label htmlFor={`lang-${value || "all"}`} className="text-sm cursor-pointer leading-none">
                {label}
              </Label>
            </div>
          ))}
        </div>
      </div>

      <Separator />

      {/* Year Range */}
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Rentang Tahun
        </p>
        <div className="flex items-center gap-2">
          <input
            type="number"
            id="year-from"
            placeholder="Dari"
            value={yearFrom}
            onChange={(e) => onYearFromChange(e.target.value)}
            min={1990}
            max={2026}
            className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <span className="text-muted-foreground text-sm shrink-0">—</span>
          <input
            type="number"
            id="year-to"
            placeholder="Sampai"
            value={yearTo}
            onChange={(e) => onYearToChange(e.target.value)}
            min={1990}
            max={2026}
            className="w-full rounded-md border border-input bg-background px-2 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      {/* Active filters summary */}
      {(selectedType || yearFrom || yearTo || language) && (
        <>
          <Separator />
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Filter Aktif
            </p>
            <div className="flex flex-wrap gap-1.5">
              {selectedType && (
                <Badge
                  variant="secondary"
                  className="text-xs gap-1 cursor-pointer"
                  onClick={() => onTypeChange(null)}
                >
                  {DOCUMENT_TYPE_LABELS[selectedType]} ×
                </Badge>
              )}
              {language && (
                <Badge
                  variant="secondary"
                  className="text-xs gap-1 cursor-pointer"
                  onClick={() => onLanguageChange("")}
                >
                  {language.toUpperCase()} ×
                </Badge>
              )}
              {(yearFrom || yearTo) && (
                <Badge variant="secondary" className="text-xs">
                  {yearFrom || "∞"} – {yearTo || "∞"}
                </Badge>
              )}
            </div>
          </div>
        </>
      )}
    </aside>
  );
}
