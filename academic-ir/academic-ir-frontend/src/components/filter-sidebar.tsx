"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { type DocumentType, DOCUMENT_TYPE_LABELS } from "@/lib/api";
import { Filter, RotateCcw } from "lucide-react";

interface FilterSidebarProps {
  selectedType: DocumentType | null;
  yearFrom: string;
  yearTo: string;
  language: string;
  onTypeChange: (type: DocumentType | null) => void;
  onYearFromChange: (value: string) => void;
  onYearToChange: (value: string) => void;
  onLanguageChange: (value: string) => void;
  onReset: () => void;
  totalResults: number;
}

const ALL_TYPES: DocumentType[] = ["MATERIAL", "RESEARCH", "THESIS"];

export function FilterSidebar({
  selectedType,
  yearFrom,
  yearTo,
  language,
  onTypeChange,
  onYearFromChange,
  onYearToChange,
  onLanguageChange,
  onReset,
  totalResults,
}: FilterSidebarProps) {
  return (
    <aside className="w-60 shrink-0 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-semibold">Filters</span>
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
        {totalResults} result{totalResults !== 1 ? "s" : ""}
      </div>

      <Separator />

      {/* Document Type */}
      <div className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Document Type
        </p>
        <div className="space-y-2">
          <div className="flex items-center gap-2.5">
            <Checkbox
              id="type-all"
              checked={selectedType === null}
              onCheckedChange={() => onTypeChange(null)}
            />
            <Label htmlFor="type-all" className="text-sm cursor-pointer leading-none">
              All types
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
          Language
        </p>
        <div className="space-y-2">
          {[
            { value: "", label: "All languages" },
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
          Year Range
        </p>
        <div className="flex items-center gap-2">
          <input
            type="number"
            id="year-from"
            placeholder="From"
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
            placeholder="To"
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
              Active Filters
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
