import type { Metadata, Viewport } from 'next'
import type { ReactNode } from 'react'
import '@econexao/ui/styles.css'
import { themeBootstrapScript, themeColors } from '@econexao/ui/theme'
import './styles.css'

export const metadata: Metadata = {
  title: 'Operação | ECOnexão',
  description: 'Painel operacional da ECOnexão.',
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
      <body>{children}</body>
    </html>
  )
}
