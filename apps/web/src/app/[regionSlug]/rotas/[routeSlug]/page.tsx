import type { Metadata } from 'next'
import { RouteExperience } from '@/components/route-experience'
import { SiteHeader } from '@/components/site-header'

interface RoutePageProps {
  params: Promise<{ regionSlug: string; routeSlug: string }>
}

function humanizeSlug(slug: string) {
  return slug
    .split('-')
    .filter(Boolean)
    .map((part) => part[0]?.toLocaleUpperCase('pt-BR') + part.slice(1))
    .join(' ')
}

export async function generateMetadata({
  params,
}: RoutePageProps): Promise<Metadata> {
  const { routeSlug } = await params

  return {
    title: humanizeSlug(routeSlug),
    description: 'Consulte informações publicadas e verificadas desta rota.',
  }
}

export default async function RoutePage({ params }: RoutePageProps) {
  const { regionSlug, routeSlug } = await params

  return (
    <>
      <SiteHeader compactOnMobile />
      <main className="route-page">
        <RouteExperience
          regionSlug={regionSlug}
          routeSlug={routeSlug}
          tab="overview"
        />
      </main>
    </>
  )
}
