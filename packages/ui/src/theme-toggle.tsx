'use client'

import { Moon, Sun } from 'lucide-react'
import { useEffect, useState } from 'react'
import {
  isTheme,
  THEME_CHANGE_EVENT,
  THEME_STORAGE_KEY,
  themeColors,
  type Theme,
} from './theme'

function preferredTheme(): Theme {
  const documentTheme = document.documentElement.dataset.theme ?? null
  if (isTheme(documentTheme)) {
    return documentTheme
  }

  return 'light'
}

function applyTheme(theme: Theme, persist: boolean) {
  document.documentElement.dataset.theme = theme
  document.documentElement.style.colorScheme = theme
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute('content', themeColors[theme])

  if (persist) {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme)
    } catch {
      // The visual preference still applies when storage is unavailable.
    }
  }

  window.dispatchEvent(
    new CustomEvent<Theme>(THEME_CHANGE_EVENT, { detail: theme }),
  )
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>('light')

  useEffect(() => {
    setTheme(preferredTheme())

    const handleThemeChange = (event: Event) => {
      setTheme((event as CustomEvent<Theme>).detail)
    }

    window.addEventListener(THEME_CHANGE_EVENT, handleThemeChange)

    return () => {
      window.removeEventListener(THEME_CHANGE_EVENT, handleThemeChange)
    }
  }, [])

  const nextTheme: Theme = theme === 'light' ? 'dark' : 'light'
  const currentLabel = theme === 'light' ? 'claro' : 'escuro'
  const nextLabel = nextTheme === 'light' ? 'claro' : 'escuro'
  const handleToggle = () => {
    applyTheme(nextTheme, true)
    setTheme(nextTheme)
  }

  return (
    <button
      aria-label={`Tema atual: ${currentLabel}. Ativar tema ${nextLabel}.`}
      aria-pressed={theme === 'dark'}
      className="ui-button ui-button--secondary"
      onClick={handleToggle}
      type="button"
    >
      <span aria-hidden="true" className="theme-toggle__icon">
        {nextTheme === 'light' ? <Sun /> : <Moon />}
      </span>
      <span className="theme-toggle__label">Usar {nextLabel}</span>
    </button>
  )
}
