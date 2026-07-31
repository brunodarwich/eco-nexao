import { ThemeToggle } from '@econexao/ui/theme-toggle'
import Image from 'next/image'
import logoHorizontal from '../../../../assets/brand/logo-horizontal.png'
import { OperationalDashboard } from './operational-dashboard'

export default function AdminHomePage() {
  return (
    <>
      <header className="admin-header">
        <Image
          alt="ECOnexão"
          className="brand-logo"
          priority
          src={logoHorizontal}
        />
        <ThemeToggle />
      </header>
      <main>
        <p className="eyebrow">Operação Editorial & Reflexo do App</p>
        <h1>Painel Operacional</h1>
        <p className="summary">
          Acompanhe os acessos ao aplicativo, o engajamento nos pontos da rota,
          a prontidão editorial e os relatos da comunidade em tempo real.
        </p>
        <OperationalDashboard />
      </main>
    </>
  )
}
