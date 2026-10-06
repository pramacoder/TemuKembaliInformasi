"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  type SuggestionResponse,
  type TolerantCorrection,
  type TolerantMode,
  fetchSuggestions,
} from "@/lib/api";
import {
  BookMarked,
  Check,
  ChevronDown,
  CornerDownLeft,
  Loader2,
  Search,
  Shield,
  Sparkles,
  Wand2,
  X,
} from "lucide-react";

interface SearchBarProps {
  query: string;
  onChange: (value: string) => void;
  onSearch: (overrideQuery?: string, overrideMode?: TolerantMode) => void;
  isLoading?: boolean;
  tolerantMode: TolerantMode;
  onTolerantModeChange: (mode: TolerantMode) => void;
}

export function SearchBar({
  query,
  onChange,
  onSearch,
  isLoading,
  tolerantMode,
  onTolerantModeChange,
}: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [suggestionsData, setSuggestionsData] = useState<SuggestionResponse | null>(null);
  const [isFetchingSuggestions, setIsFetchingSuggestions] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const [showModeDropdown, setShowModeDropdown] = useState(false);

  // Debounced suggestion fetch
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setSuggestionsData(null);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setIsFetchingSuggestions(true);
        const data = await fetchSuggestions(trimmed, 6);
        setSuggestionsData(data);
        if (
          (data.suggestions && data.suggestions.length > 0) ||
          (data.did_you_mean && data.did_you_mean.toLowerCase() !== trimmed.toLowerCase())
        ) {
          setShowDropdown(true);
        } else {
          setShowDropdown(false);
        }
      } catch {
        // Silently handle suggestion failure
        setSuggestionsData(null);
      } finally {
        setIsFetchingSuggestions(false);
      }
    }, 220);

    return () => clearTimeout(timer);
  }, [query]);

  // Click outside to dismiss dropdowns
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
        setShowModeDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Collect all selectable items for keyboard navigation
  const selectableItems: string[] = [];
  if (
    suggestionsData?.did_you_mean &&
    suggestionsData.did_you_mean.toLowerCase() !== query.trim().toLowerCase()
  ) {
    selectableItems.push(suggestionsData.did_you_mean);
  }
  if (suggestionsData?.suggestions) {
    for (const s of suggestionsData.suggestions) {
      if (!selectableItems.includes(s) && s.toLowerCase() !== query.trim().toLowerCase()) {
        selectableItems.push(s);
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!showDropdown && selectableItems.length > 0) {
        setShowDropdown(true);
        setSelectedIndex(0);
      } else {
        setSelectedIndex((prev) => (prev < selectableItems.length - 1 ? prev + 1 : -1));
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > -1 ? prev - 1 : selectableItems.length - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < selectableItems.length) {
        const chosen = selectableItems[selectedIndex];
        onChange(chosen);
        setShowDropdown(false);
        onSearch(chosen);
      } else {
        setShowDropdown(false);
        onSearch(query);
      }
    } else if (e.key === "Escape") {
      setShowDropdown(false);
      setSelectedIndex(-1);
    }
  };

  const handleSelectSuggestion = (text: string) => {
    onChange(text);
    setShowDropdown(false);
    onSearch(text);
  };

  const getCorrectionBadge = (corr?: TolerantCorrection) => {
    if (!corr) return null;
    switch (corr.type) {
      case "typo":
        return (
          <Badge className="text-[10px] h-4.5 px-1.5 bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30">
            Typo
          </Badge>
        );
      case "abbreviation":
        return (
          <Badge className="text-[10px] h-4.5 px-1.5 bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30">
            Singkatan
          </Badge>
        );
      case "spelling":
        return (
          <Badge className="text-[10px] h-4.5 px-1.5 bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
            Ejaan
          </Badge>
        );
      case "technical":
        return (
          <Badge className="text-[10px] h-4.5 px-1.5 bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30">
            Teknis
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-[10px] h-4.5 px-1.5">
            {corr.type}
          </Badge>
        );
    }
  };

  const modeDescriptions: Record<
    TolerantMode,
    { label: string; tag: string; icon: React.ComponentType<{ className?: string }> }
  > = {
    auto: {
      label: "Otomatis (Fallback)",
      tag: "Exact First + Fallback",
      icon: Sparkles,
    },
    always: {
      label: "Selalu Aktif",
      tag: "Koreksi Agresif",
      icon: Wand2,
    },
    off: {
      label: "Nonaktif",
      tag: "Pencarian Eksak Murni",
      icon: Shield,
    },
  };

  const CurrentModeIcon = modeDescriptions[tolerantMode].icon;

  return (
    <div ref={containerRef} className="relative w-full max-w-3xl flex flex-col gap-2">
      {/* Search Bar Input Row */}
      <div className="flex gap-2 w-full">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />

          <Input
            ref={inputRef}
            id="search-input"
            type="search"
            placeholder="Cari artikel ilmiah, bahan kuliah, skripsi, atau istilah teknis…"
            value={query}
            onChange={(e) => {
              onChange(e.target.value);
              setSelectedIndex(-1);
            }}
            onFocus={() => {
              if (selectableItems.length > 0) setShowDropdown(true);
            }}
            onKeyDown={handleKeyDown}
            className="pl-10 pr-20 h-12 text-base shadow-xs transition-all focus-visible:ring-2"
            autoComplete="off"
            suppressHydrationWarning
          />

          {/* Right icons inside input: Spinner / Clear */}
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
            {isFetchingSuggestions && (
              <Loader2 className="h-4 w-4 text-muted-foreground animate-spin" />
            )}
            {query && (
              <button
                type="button"
                onClick={() => {
                  onChange("");
                  setSuggestionsData(null);
                  setShowDropdown(false);
                  inputRef.current?.focus();
                }}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors"
                title="Hapus pencarian"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Tolerant Mode Quick Switcher */}
        <div className="relative">
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowModeDropdown((prev) => !prev)}
            className="h-12 px-3 gap-1.5 text-xs font-medium border-border/80 bg-background/80 hover:bg-muted/80"
            title="Pengaturan Mode Tolerant Retrieval"
          >
            <CurrentModeIcon
              className={`h-3.5 w-3.5 ${
                tolerantMode === "auto"
                  ? "text-primary"
                  : tolerantMode === "always"
                  ? "text-amber-500"
                  : "text-muted-foreground"
              }`}
            />
            <span className="hidden md:inline">{modeDescriptions[tolerantMode].label}</span>
            <ChevronDown className="h-3 w-3 opacity-60" />
          </Button>

          {/* Mode Selector Dropdown */}
          {showModeDropdown && (
            <div className="absolute right-0 top-full mt-1.5 w-64 rounded-lg border bg-popover text-popover-foreground shadow-lg z-50 p-1.5 text-xs space-y-1 animate-in fade-in-50 zoom-in-95">
              <div className="px-2 py-1 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                Mode Tolerant Retrieval
              </div>
              {(["auto", "always", "off"] as TolerantMode[]).map((mode) => {
                const Icon = modeDescriptions[mode].icon;
                const isSelected = tolerantMode === mode;
                return (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => {
                      onTolerantModeChange(mode);
                      setShowModeDropdown(false);
                    }}
                    className={`w-full text-left px-2.5 py-2 rounded-md flex items-start justify-between gap-2 transition-colors ${
                      isSelected
                        ? "bg-primary/10 text-primary font-medium"
                        : "hover:bg-muted text-foreground"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4 shrink-0 mt-0.5" />
                      <div>
                        <p className="font-semibold">{modeDescriptions[mode].label}</p>
                        <p className="text-[11px] text-muted-foreground">
                          {modeDescriptions[mode].tag}
                        </p>
                      </div>
                    </div>
                    {isSelected && <Check className="h-3.5 w-3.5 mt-1 shrink-0 text-primary" />}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Submit Search Button */}
        <Button
          id="search-button"
          onClick={() => {
            setShowDropdown(false);
            onSearch();
          }}
          disabled={isLoading}
          size="lg"
          className="h-12 px-6 gap-2 shadow-xs"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
          Cari
        </Button>
      </div>

      {/* Floating Suggestions & Did-You-Mean Dropdown */}
      {showDropdown && selectableItems.length > 0 && (
        <div className="absolute left-0 right-0 top-full mt-1.5 bg-background border rounded-lg shadow-xl z-50 overflow-hidden divide-y text-sm animate-in fade-in-50 zoom-in-95">
          {/* Section: Did You Mean banner */}
          {suggestionsData?.did_you_mean &&
            suggestionsData.did_you_mean.toLowerCase() !== query.trim().toLowerCase() && (
              <div
                onClick={() => handleSelectSuggestion(suggestionsData.did_you_mean!)}
                className={`p-3 bg-primary/5 hover:bg-primary/10 cursor-pointer flex items-center justify-between gap-3 transition-colors ${
                  selectedIndex === 0 ? "bg-primary/15" : ""
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="h-7 w-7 rounded-full bg-primary/15 text-primary flex items-center justify-center shrink-0">
                    <Sparkles className="h-3.5 w-3.5" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs text-muted-foreground">Mungkin maksud Anda:</p>
                    <p className="font-semibold text-primary truncate">
                      {suggestionsData.did_you_mean}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant="outline" className="text-[10px] text-muted-foreground">
                    {Math.round(suggestionsData.confidence * 100)}% match
                  </Badge>
                  <Button size="sm" variant="ghost" className="h-7 text-xs gap-1 text-primary">
                    Gunakan
                    <CornerDownLeft className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            )}

          {/* Section: Suggestions & Typos List */}
          <div className="p-1 space-y-0.5">
            <div className="px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground flex items-center justify-between">
              <span>Saran Pencarian Cerdas</span>
              <span>Gunakan panah ↑↓ untuk navigasi</span>
            </div>

            {selectableItems.map((item, idx) => {
              // Find matching correction if any
              const matchingCorr = suggestionsData?.corrections.find(
                (c) => c.target.toLowerCase() === item.toLowerCase()
              );
              const isSelected = selectedIndex === idx;

              return (
                <div
                  key={idx}
                  onClick={() => handleSelectSuggestion(item)}
                  className={`px-3 py-2 rounded-md flex items-center justify-between gap-2 cursor-pointer transition-colors ${
                    isSelected ? "bg-muted text-foreground font-medium" : "hover:bg-muted/70 text-foreground"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Search className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    <span className="truncate">{item}</span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    {getCorrectionBadge(matchingCorr)}
                    {matchingCorr && (
                      <span className="text-[11px] text-muted-foreground hidden sm:inline">
                        ({matchingCorr.source} → {matchingCorr.target})
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer note */}
          <div className="px-3 py-1.5 bg-muted/30 text-[11px] text-muted-foreground flex items-center justify-between">
            <span>Tolerant Retrieval: typo, singkatan, ejaan baku &amp; istilah teknis</span>
            <span className="font-mono text-[10px]">BM25 Lexical Layer</span>
          </div>
        </div>
      )}
    </div>
  );
}

export function AppHeader() {
  return (
    <header className="border-b bg-background/95 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center h-14 gap-3">
          <div className="flex items-center gap-2 shrink-0">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <BookMarked className="h-4 w-4 text-primary-foreground" />
            </div>
            <div>
              <p className="text-sm font-bold leading-none">Academic IR</p>
              <p className="text-[10px] text-muted-foreground leading-none mt-0.5">
                Information Retrieval
              </p>
            </div>
          </div>

          <div className="h-5 w-px bg-border mx-2" />

          <nav className="flex items-center gap-1 text-sm text-muted-foreground">
            <Button variant="ghost" size="sm" className="h-7 text-xs">
              Pencarian
            </Button>
            <Button variant="ghost" size="sm" className="h-7 text-xs">
              Koleksi Dokumen
            </Button>
            <Button variant="ghost" size="sm" className="h-7 text-xs">
              Tentang
            </Button>
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <Badge variant="outline" className="text-[10px] gap-1 text-primary border-primary/30">
              <Sparkles className="h-2.5 w-2.5" />
              Tolerant Retrieval Ready
            </Badge>
          </div>
        </div>
      </div>
    </header>
  );
}
