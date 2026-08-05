import { afterEach, describe, expect, it, vi } from 'vitest'
import { savePoiDraft } from './poi-draft'

const originalFetch = globalThis.fetch

afterEach(() => {
  globalThis.fetch = originalFetch
  vi.restoreAllMocks()
})

describe('POI draft workflow client', () => {
  const input = {
    actorId: '00000000-0000-0000-0000-000000000002',
    address: 'Comunidade de teste',
    category: 'Hospedagem',
    displayName: 'Pousada de teste',
    phone: '+5593999999999',
    regionId: '00000000-0000-0000-0000-000000000001',
  }

  it('sends domain UUIDs and always creates a draft snapshot', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ csrf_token: 'csrf-test' }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            snapshot: { status: 'Rascunho' },
            target_id: input.actorId,
          }),
          { status: 201 },
        ),
      )

    await savePoiDraft(input)

    const request = vi.mocked(globalThis.fetch).mock.calls[1][1]
    expect(JSON.parse(String(request?.body))).toEqual({
      region_id: input.regionId,
      snapshot: {
        address: input.address,
        category: input.category,
        display_name: input.displayName,
        phone: input.phone,
        status: 'Rascunho',
      },
      target_id: input.actorId,
      target_type: 'actor',
    })
  })

  it('rejects API failures instead of returning a local success', async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ csrf_token: 'csrf-test' }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ message: 'Workflow indisponível.' }), {
          status: 503,
        }),
      )

    await expect(savePoiDraft(input)).rejects.toMatchObject({
      kind: 'server-error',
      message: 'Workflow indisponível.',
      status: 503,
    })
  })
})
