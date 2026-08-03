export const THEME_STORAGE_KEY = 'econexao-theme'
export const THEME_CHANGE_EVENT = 'econexao:theme-change'

export type Theme = 'light' | 'dark'

export const themeColors: Record<Theme, string> = {
  light: '#f7f8f5',
  dark: '#090d09',
}

export function isTheme(value: string | null): value is Theme {
  return value === 'light' || value === 'dark'
}

export const themeBootstrapScript = String.raw`
(() => {
  const storageKey = '${THEME_STORAGE_KEY}';
  let storedTheme = null;

  try {
    storedTheme = window.localStorage.getItem(storageKey);
  } catch {}

  const theme =
    storedTheme === 'light' || storedTheme === 'dark'
      ? storedTheme
      : window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
  const root = document.documentElement;
  root.dataset.theme = theme;
  root.style.colorScheme = theme;

  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute('content', theme === 'dark' ? '${themeColors.dark}' : '${themeColors.light}');
  }
})();
`
