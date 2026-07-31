import { describe, expect, it } from 'vitest'
import { isTheme, themeBootstrapScript, themeColors } from '@econexao/ui/theme'

describe('public theme foundation', () => {
  it('accepts only supported persisted themes', () => {
    expect(isTheme('light')).toBe(true)
    expect(isTheme('dark')).toBe(true)
    expect(isTheme('system')).toBe(false)
    expect(isTheme(null)).toBe(false)
  })

  it('bootstraps the light default and persisted theme before hydration', () => {
    expect(themeBootstrapScript).toContain(": 'light'")
    expect(themeBootstrapScript).not.toContain('prefers-color-scheme: dark')
    expect(themeBootstrapScript).toContain('theme-color')
    expect(themeBootstrapScript).toContain('localStorage')
  })

  it('uses the approved near-black background in dark mode', () => {
    expect(themeColors.dark).toBe('#090d09')
  })
})
