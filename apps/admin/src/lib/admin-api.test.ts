import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  AdminApiError,
  adminMutation,
  adminRequest,
  fetchDashboardSummary,
  getAdminRequestError,
} from './admin-api'

const originalFetch = globalThis.fetch

afterEach(() => {
  globalThis.fetch = originalFetch
  vi.restoreAllMocks()
})

describe('admin API client', () => {
  it('preserves credentials and the admin proxy for reads', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ authenticated: true }), { status: 200 }),
      )

    await adminRequest('auth/session')

    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/admin/auth/session',
      expect.objectContaining({
        cache: 'no-store',
        credentials: 'include',
      }),
    )
  })

  it('obtains CSRF once and sends it with a mutation', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ csrf_token: 'csrf-test' }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: 'revision-id' }), { status: 201 }),
      )

    await adminMutation('editorial/revisions', {
      body: JSON.stringify({ snapshot: {} }),
      headers: { 'Content-Type': 'application/json' },
      method: 'POST',
    })

    const mutation = vi.mocked(globalThis.fetch).mock.calls[1]
    expect(mutation[0]).toBe('/api/admin/editorial/revisions')
    expect(new Headers(mutation[1]?.headers).get('X-CSRFToken')).toBe(
      'csrf-test',
    )
    expect(mutation[1]?.credentials).toBe('include')
  })

  it('translates HTTP failures without returning a successful payload', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ message: 'Sem permissão regional.' }), {
        status: 403,
      }),
    )

    await expect(adminRequest('reports/')).rejects.toMatchObject({
      kind: 'forbidden',
      message: 'Sem permissão regional.',
      status: 403,
    })
  })

  it('classifies network failures as unavailable', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('offline'))

    const error = await adminRequest('reports/').catch((caught) => caught)
    expect(error).toBeInstanceOf(AdminApiError)
    expect(getAdminRequestError(error)).toBe('unavailable')
  })

  it('fetches dashboard summary with region query parameter', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          active_alerts_count: 1,
          pending_revisions_count: 2,
          priority_reports_count: 1,
          region_slug: 'alter-do-chao',
        }),
        { status: 200 },
      ),
    )

    const summary = await fetchDashboardSummary('alter-do-chao')

    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/admin/dashboard/summary?region_slug=alter-do-chao',
      expect.objectContaining({
        cache: 'no-store',
        credentials: 'include',
      }),
    )
    expect(summary).toEqual({
      active_alerts_count: 1,
      pending_revisions_count: 2,
      priority_reports_count: 1,
      region_slug: 'alter-do-chao',
    })
  })
})
