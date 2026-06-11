'use client';

import { useFintelliTheme } from '@/lib/fintelli/theme';

export function ThemeDock() {
  const { theme, setTheme } = useFintelliTheme();
  return (
    <div className="theme-dock">
      <div>
        <button
          type="button"
          className={`tdock-btn ${theme === 'light' ? 'on' : ''}`}
          onClick={() => setTheme('light')}
          title="Light"
        >
          ☀️
        </button>
        <div className="tdock-lbl">Light</div>
      </div>
      <div>
        <button
          type="button"
          className={`tdock-btn ${theme === 'dark' ? 'on' : ''}`}
          onClick={() => setTheme('dark')}
          title="Dark"
        >
          🌑
        </button>
        <div className="tdock-lbl">Dark</div>
      </div>
    </div>
  );
}
