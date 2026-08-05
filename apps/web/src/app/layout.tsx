import type { Metadata, Viewport } from 'next'
import type { ReactNode } from 'react'
import 'maplibre-gl/dist/maplibre-gl.css'
import '@econexao/ui/styles.css'
import { themeBootstrapScript, themeColors } from '@econexao/ui/theme'
import { AnalyticsConsentBanner } from '../components/analytics-consent'
import { AnalyticsLifecycle } from '../components/analytics-lifecycle'
import './styles.css'
import './public-shell.css'

export const metadata: Metadata = {
  title: {
    default: 'ECOnexão',
    template: '%s | ECOnexão',
  },
  description: 'Rotas confiáveis e conexões locais para descobrir destinos.',
}

export const viewport: Viewport = {
  initialScale: 1,
  width: 'device-width',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <meta content={themeColors.light} name="theme-color" />
        <script dangerouslySetInnerHTML={{ __html: themeBootstrapScript }} />
      </head>
      <body>
        {children}
        <AnalyticsLifecycle />
        <AnalyticsConsentBanner />
      </body>
    </html>
  )
}
