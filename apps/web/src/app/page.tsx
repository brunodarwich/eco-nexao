import { PublicAppShell } from '@/components/public-app-shell'
import { RegionPicker } from '@/components/region-picker'

export default function HomePage() {
  return (
    <PublicAppShell current="home" title="Escolha seu território">
      <div className="home-page">
        <section className="hero hero--compact" aria-labelledby="hero-title">
          <p className="eyebrow">Escolha seu território</p>
          <h1 id="hero-title">Onde você quer se conectar?</h1>
          <p className="hero__summary">
            Selecione uma região para ver somente rotas e experiências daquele
            território. Você poderá trocar depois.
          </p>
        </section>
        <section aria-label="Seleção de região">
          <RegionPicker />
        </section>
      </div>
    </PublicAppShell>
  )
}
