'use client';

import { createContext, useCallback, useContext, useEffect, useState } from 'react';

export type FintelliTheme = 'light' | 'dark';

const STORAGE_KEY = 'fintelli_theme';

const ThemeContext = createContext<{
  theme: FintelliTheme;
  setTheme: (t: FintelliTheme) => void;
}>({ theme: 'light', setTheme: () => {} });

export function FintelliThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<FintelliTheme>('light');

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as FintelliTheme | null;
    if (stored === 'light' || stored === 'dark') setThemeState(stored);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = useCallback((t: FintelliTheme) => setThemeState(t), []);

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
}

export function useFintelliTheme() {
  return useContext(ThemeContext);
}
