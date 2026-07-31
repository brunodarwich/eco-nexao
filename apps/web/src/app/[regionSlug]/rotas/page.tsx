import type { Metadata } from 'next'
import { PublicAppShell } from '@/components/public-app-shell'
import { RoutesExplorer } from '@/components/routes-explorer'
import { filtersFromSearchParams } from '@/lib/route-filters'

interface RoutesPageProps {
  params: Promise<{ regionSlug: string }>
  searchParams: Promise<Record<string, string | string[] | undefined>>
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
}: RoutesPageProps): Promise<Metadata> {
  const { regionSlug } = await params
  const regionName = humanizeSlug(regionSlug)

  return {
    title: `Rotas em ${regionName}`,
    description: `Descubra rotas publicadas e experiências locais em ${regionName}.`,
  }
}

export default async function RoutesPage({
  params,
  searchParams,
}: RoutesPageProps) {
  const [{ regionSlug }, resolvedSearchParams] = await Promise.all([
    params,
    searchParams,
  ])

  return (
    <PublicAppShell
      current="routes"
      regionSlug={regionSlug}
      title="Descoberta de rotas"
    >
      <div className="routes-page">
        <RoutesExplorer
          initialFilters={filtersFromSearchParams(resolvedSearchParams)}
          regionSlug={regionSlug}
        />
      </div>
    </PublicAppShell>
  )
}
