import type { Metadata } from 'next'
import { RouteExperience } from '@/components/route-experience'
import { SiteHeader } from '@/components/site-header'

interface RouteMapPageProps {
  params: Promise<{ regionSlug: string; routeSlug: string }>
}

export const metadata: Metadata = {
  title: 'Mapa da rota',
  description: 'Consulte o percurso e a alternativa textual da rota.',
}

export default async function RouteMapPage({ params }: RouteMapPageProps) {
  const { regionSlug, routeSlug } = await params

  return (
    <>
      <SiteHeader compactOnMobile />
      <main className="route-page">
        <RouteExperience
          regionSlug={regionSlug}
          routeSlug={routeSlug}
          tab="map"
        />
      </main>
    </>
  )
}
