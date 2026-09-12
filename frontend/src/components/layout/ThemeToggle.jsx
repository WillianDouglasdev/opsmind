import { Moon, Sun } from "lucide-react";
import { useState } from "react";
import {
  applyTheme,
  getInitialTheme,
  oppositeTheme,
  persistTheme,
  themeControlLabel,
} from "../../utils/theme.js";

function initialTheme() {
  if (typeof document === "undefined") return "light";
  return document.documentElement.dataset.theme || getInitialTheme({
    storage: window.localStorage,
    mediaQuery: window.matchMedia("(prefers-color-scheme: dark)"),
  });
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState(initialTheme);
  const label = themeControlLabel(theme);

  function toggleTheme() {
    const nextTheme = oppositeTheme(theme);
    // Aplicamos antes de atualizar o estado para que shell e canvas mudem no mesmo frame.
    applyTheme(nextTheme, {
      root: document.documentElement,
      meta: document.querySelector('meta[name="theme-color"]'),
    });
    persistTheme(nextTheme, window.localStorage);
    setTheme(nextTheme);
  }

  return (
    <button className="theme-toggle" type="button" onClick={toggleTheme} aria-label={label} title={label} aria-pressed={theme === "dark"}>
      {theme === "dark" ? <Sun size={16} aria-hidden="true" /> : <Moon size={16} aria-hidden="true" />}
      <span>{theme === "dark" ? "Claro" : "Escuro"}</span>
    </button>
  );
}
