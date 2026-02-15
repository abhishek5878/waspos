"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

interface SearchContextType {
  search: string;
  setSearch: (s: string) => void;
}

const SearchContext = createContext<SearchContextType | null>(null);

export function SearchProvider({ children }: { children: ReactNode }) {
  const [search, setSearch] = useState("");
  return (
    <SearchContext.Provider value={{ search, setSearch }}>
      {children}
    </SearchContext.Provider>
  );
}

export function useSearch() {
  const ctx = useContext(SearchContext);
  if (!ctx) {
    return { search: "", setSearch: () => {} };
  }
  return ctx;
}
