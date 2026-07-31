import type { RouteSummary } from './public-api'

export type DifficultyFilter = '' | RouteSummary['difficulty']
export type DurationFilter = '' | 'short' | 'medium' | 'long'

export interface RouteFilters {
  difficulty: DifficultyFilter
  duration: DurationFilter
  query: string
}

const durationRanges: Record<
  Exclude<DurationFilter, ''>,
  (minutes: number) => boolean
> = {
  short: (minutes) => minutes < 120,
  medium: (minutes) => minutes >= 120 && minutes <= 240,
  long: (minutes) => minutes > 240,
}

export function filterRoutes(routes: RouteSummary[], filters: RouteFilters) {
  const normalizedQuery = filters.query.trim().toLocaleLowerCase('pt-BR')

  return routes.filter((route) => {
    const matchesQuery =
      normalizedQuery.length === 0 ||
      `${route.public_name} ${route.short_promise}`
        .toLocaleLowerCase('pt-BR')
        .includes(normalizedQuery)
    const matchesDifficulty =
      filters.difficulty === '' || route.difficulty === filters.difficulty
    const matchesDuration =
      filters.duration === '' ||
      durationRanges[filters.duration](route.duration_minutes)

    return matchesQuery && matchesDifficulty && matchesDuration
  })
}

export function filtersFromSearchParams(
  searchParams: Record<string, string | string[] | undefined>,
): RouteFilters {
  const query = typeof searchParams.q === 'string' ? searchParams.q : ''
  const difficulty =
    searchParams.difficulty === 'easy' ||
    searchParams.difficulty === 'moderate' ||
    searchParams.difficulty === 'hard'
      ? searchParams.difficulty
      : ''
  const duration =
    searchParams.duration === 'short' ||
    searchParams.duration === 'medium' ||
    searchParams.duration === 'long'
      ? searchParams.duration
      : ''

  return { difficulty, duration, query }
}
