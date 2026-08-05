import { afterEach, describe, expect, it, vi } from 'vitest'
import { GET } from './route'

describe('proxy público do painel', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('preserva indisponibilidade como erro em vez de lista vazia', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))

    const response = await GET(
      new Request('http://localhost/api/public/regions'),
      { params: Promise.resolve({ path: ['regions'] }) },
    )

    expect(response.status).toBe(502)
    await expect(response.json()).resolves.toMatchObject({
      code: 'public_api_unavailable',
    })
  })
})
