import { describe, expect, it } from 'vitest'
import { toDashboardRoute } from './dashboard-routes'

describe('toDashboardRoute', () => {
  it('maps only equivalent public route fields and leaves readiness absent', () => {
    const route = toDashboardRoute({
      duration_minutes: 240,
      public_name: 'Rota de Pindobal',
      slug: 'pindobal',
    })

    expect(route).toEqual({
      durationMinutes: 240,
      slug: 'pindobal',
      title: 'Rota de Pindobal',
    })
    expect(route.readiness).toBeUndefined()
  })
})
