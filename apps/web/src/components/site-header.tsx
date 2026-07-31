import { ThemeToggle } from '@econexao/ui/theme-toggle'
import Image from 'next/image'
import Link from 'next/link'
import logoHorizontal from '../../../../assets/brand/logo-horizontal.png'

interface SiteHeaderProps {
  compactOnMobile?: boolean
}

export function SiteHeader({ compactOnMobile = false }: SiteHeaderProps) {
  return (
    <header
      className={`site-header${compactOnMobile ? ' site-header--route' : ''}`}
    >
      <Link aria-label="ECOnexão — início" className="brand-link" href="/">
        <Image alt="" className="brand-logo" priority src={logoHorizontal} />
      </Link>
      <ThemeToggle />
    </header>
  )
}
