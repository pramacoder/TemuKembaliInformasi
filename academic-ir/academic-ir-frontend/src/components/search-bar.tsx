"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { BookMarked, Search } from "lucide-react";
import { useRef } from "react";

interface SearchBarProps {
  query: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  isLoading?: boolean;
}

export function SearchBar({ query, onChange, onSearch, isLoading }: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") onSearch();
  };

  return (
    <div className="flex gap-2 w-full max-w-3xl">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <Input
          ref={inputRef}
          id="search-input"
          type="search"
          placeholder="Search academic documents, authors, keywords…"
          value={query}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          className="pl-9 h-11 text-base"
          autoComplete="off"
        />
      </div>
      <Button
        id="search-button"
        onClick={onSearch}
        disabled={isLoading}
        size="lg"
        className="h-11 px-6 gap-2"
      >
        <Search className="h-4 w-4" />
        Search
      </Button>
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
              Search
            </Button>
            <Button variant="ghost" size="sm" className="h-7 text-xs">
              Collections
            </Button>
            <Button variant="ghost" size="sm" className="h-7 text-xs">
              About
            </Button>
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <span className="text-xs text-muted-foreground hidden sm:inline">
              6 documents indexed
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
