'use client';

import { useEffect, useRef, useState } from 'react';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/lib/api';

interface DrugNameInputProps {
  id: string;
  value: string;
  onChange: (value: string) => void;
  label: string;
}

export function DrugNameInput({ id, value, onChange, label }: DrugNameInputProps) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const timer = useRef<number | undefined>(undefined);
  const latestQuery = useRef('');

  useEffect(() => () => window.clearTimeout(timer.current), []);

  const search = (query: string) => {
    window.clearTimeout(timer.current);
    const trimmed = query.trim();
    latestQuery.current = trimmed;
    if (trimmed.length < 2) {
      setSuggestions([]);
      return;
    }
    timer.current = window.setTimeout(async () => {
      try {
        const result = await apiClient.searchDrugs(trimmed, 8);
        if (latestQuery.current === trimmed) setSuggestions(result.results);
      } catch (err) {
        console.error('Drug search failed:', err);
      }
    }, 250);
  };

  return (
    <div className="relative">
      <Input
        id={id}
        aria-label={label}
        autoComplete="off"
        placeholder="Brand or generic name"
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          search(e.target.value);
        }}
        onKeyDown={(e) => {
          if (e.key === 'Escape') setSuggestions([]);
        }}
        onBlur={() => {
          window.clearTimeout(timer.current);
          latestQuery.current = '';
          // Delay so a click on a suggestion lands before the list unmounts.
          window.setTimeout(() => setSuggestions([]), 150);
        }}
      />
      {suggestions.length > 0 && (
        <ul className="absolute z-20 mt-1 max-h-64 w-full overflow-y-auto rounded-md border bg-background py-1 shadow-lg">
          {suggestions.map((name) => (
            <li key={name}>
              <button
                type="button"
                onClick={() => {
                  onChange(name);
                  setSuggestions([]);
                }}
                className="w-full px-3 py-1.5 text-left text-sm hover:bg-accent focus:bg-accent focus:outline-none"
              >
                {name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
