export const THEME_STORAGE_KEY = "opsmind-theme";
export const THEMES = ["light", "dark"];

export function resolveTheme(savedTheme, prefersDark = false) {
  if (THEMES.includes(savedTheme)) return savedTheme;
  return prefersDark ? "dark" : "light";
}

export function getInitialTheme({ storage, mediaQuery } = {}) {
  let savedTheme = null;
  try {
    savedTheme = storage?.getItem(THEME_STORAGE_KEY) ?? null;
  } catch {
    // Armazenamento pode estar indisponível em modo privado; a preferência do sistema continua válida.
  }
  return resolveTheme(savedTheme, Boolean(mediaQuery?.matches));
}

export function applyTheme(theme, { root, meta } = {}) {
  const safeTheme = resolveTheme(theme);
  if (root) {
    root.dataset.theme = safeTheme;
    root.style.colorScheme = safeTheme;
  }
  if (meta) meta.setAttribute("content", safeTheme === "dark" ? "#090b0d" : "#fafaf7");
  return safeTheme;
}

export function persistTheme(theme, storage) {
  const safeTheme = resolveTheme(theme);
  try {
    storage?.setItem(THEME_STORAGE_KEY, safeTheme);
    return true;
  } catch {
    return false;
  }
}

export function oppositeTheme(theme) {
  return theme === "dark" ? "light" : "dark";
}

export function themeControlLabel(theme) {
  return theme === "dark" ? "Ativar tema claro" : "Ativar tema escuro";
}
