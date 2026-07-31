import { ThemeToggle } from '@econexao/ui/theme-toggle'
import { Compass, Home, MapPinned, Route } from 'lucide-react'
import Image from 'next/image'
import Link from 'next/link'
import type { ReactNode } from 'react'
import logoHorizontal from '../../../../assets/brand/logo-horizontal.png'

interface PublicAppShellProps {
  children: ReactNode
  current: 'home' | 'routes'
  regionSlug?: string
  title: string
}

export function PublicAppShell({
  children,
  current,
  regionSlug,
  title,
}: PublicAppShellProps) {
  const routesHref = regionSlug ? `/${regionSlug}/rotas` : null

  return (
    <div className="public-app-shell">
      <aside className="desktop-sidebar">
        <Link aria-label="ECOnexão — início" className="sidebar-brand" href="/">
          <Image
            alt=""
            className="sidebar-brand__logo"
            priority
            src={logoHorizontal}
          />
        </Link>
        <nav aria-label="Navegação pública" className="sidebar-nav">
          <Link
            aria-current={current === 'home' ? 'page' : undefined}
            href="/?trocar=true"
          >
            <Home aria-hidden="true" />
            Trocar região
          </Link>
          {routesHref ? (
            <Link
              aria-current={current === 'routes' ? 'page' : undefined}
              href={routesHref}
            >
              <Route aria-hidden="true" />
              Rotas
            </Link>
          ) : null}
        </nav>
        <div className="sidebar-context">
          <MapPinned aria-hidden="true" />
          <div>
            <strong>Turismo consciente</strong>
            <span>Conteúdo publicado e verificável.</span>
          </div>
        </div>
      </aside>

      <div className="public-app-shell__content">
        <header className="desktop-top-bar">
          <Link
            aria-label="ECOnexão — início"
            className="mobile-brand"
            href="/"
          >
            <Image alt="" priority src={logoHorizontal} />
          </Link>
          <div className="top-bar-title">
            <Compass aria-hidden="true" />
            <span>{title}</span>
          </div>
          <ThemeToggle />
        </header>
        <main className="public-workspace">{children}</main>
      </div>
    </div>
  )
}
