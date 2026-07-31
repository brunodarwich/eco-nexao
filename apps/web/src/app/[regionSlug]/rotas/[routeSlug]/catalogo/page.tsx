import type { Metadata } from 'next'
import { RouteExperience } from '@/components/route-experience'
import { SiteHeader } from '@/components/site-header'

interface RouteCatalogPageProps {
  params: Promise<{ regionSlug: string; routeSlug: string }>
  searchParams: Promise<{ ator?: string | string[] }>
}

export const metadata: Metadata = {
  title: 'Catálogo da rota',
  description:
    'Encontre conexões locais e contatos autorizados relacionados à rota.',
}

export default async function RouteCatalogPage({
  params,
  searchParams,
}: RouteCatalogPageProps) {
  const [{ regionSlug, routeSlug }, query] = await Promise.all([
    params,
    searchParams,
  ])
  const initialActorSlug =
    typeof query.ator === 'string' ? query.ator : undefined

  return (
    <>
      <SiteHeader compactOnMobile />
      <main className="route-page">
        <RouteExperience
          initialActorSlug={initialActorSlug}
          regionSlug={regionSlug}
          routeSlug={routeSlug}
          tab="catalog"
        />
      </main>
    </>
  )
}
