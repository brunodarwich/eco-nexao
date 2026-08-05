import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  CONSENT_CHANGE_EVENT,
  CONSENT_KEY,
  QUEUE_KEY,
  flushEvents,
  getConsentChoice,
  sanitizeProperties,
  setConsentChoice,
  trackEvent,
} from './analytics-sdk'

function createMemoryStorage() {
  const store = new Map<string, string>()
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => store.set(key, value),
    removeItem: (key: string) => store.delete(key),
    clear: () => store.clear(),
  }
}

describe('Analytics SDK and LGPD Consent', () => {
  let memoryStorage: ReturnType<typeof createMemoryStorage>

  beforeEach(() => {
    memoryStorage = createMemoryStorage()
    vi.stubGlobal('window', {
      localStorage: memoryStorage,
      dispatchEvent: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })
    vi.stubGlobal('localStorage', memoryStorage)
    vi.restoreAllMocks()
  })

  it('defaults to null consent and does not track events', async () => {
    expect(getConsentChoice()).toBeNull()
    await trackEvent('session_opened', { region_id: 'regiao-teste' })
    expect(memoryStorage.getItem(QUEUE_KEY)).toBeNull()
  })

  it('clears queue when user chooses necessary only', () => {
    memoryStorage.setItem(QUEUE_KEY, JSON.stringify([{ event_name: 'test' }]))
    setConsentChoice('necessary')
    expect(getConsentChoice()).toBe('necessary')
    expect(memoryStorage.getItem(QUEUE_KEY)).toBeNull()
  })

  it('filters out PII keys from event properties', () => {
    const rawProps = {
      source: 'card_click',
      email: 'sensitive@example.com',
      phone: '+5593999999999',
      latitude: -2.56,
      longitude: -54.97,
      category_id: 'restaurante',
    }
    const cleanProps = sanitizeProperties(rawProps)
    expect(cleanProps).toEqual({
      source: 'card_click',
      category_id: 'restaurante',
    })
    expect(cleanProps).not.toHaveProperty('email')
    expect(cleanProps).not.toHaveProperty('phone')
    expect(cleanProps).not.toHaveProperty('latitude')
    expect(cleanProps).not.toHaveProperty('longitude')
  })

  it('enqueues events when consent is granted', async () => {
    setConsentChoice('granted')
    global.fetch = vi.fn().mockResolvedValue({ ok: true })

    await trackEvent('route_opened', {
      region_id: 'santarem-alter-do-chao',
      route_id: 'pindobal',
    })

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/public/events/batch',
      expect.any(Object),
    )
    const request = vi.mocked(global.fetch).mock.calls[0][1]!
    const body = JSON.parse(request.body as string)
    expect(body.consent_granted).toBe(true)
    expect(body.events[0]).not.toHaveProperty('anonymous_id')
    expect(body.events[0]).not.toHaveProperty('session_id')
    expect(body.events[0]).not.toHaveProperty('properties')
  })

  it('persists consent and notifies the active tab when preferences change', () => {
    const dispatchEvent = vi.fn()
    vi.stubGlobal('window', {
      localStorage: memoryStorage,
      dispatchEvent,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })

    setConsentChoice('granted')

    expect(memoryStorage.getItem(CONSENT_KEY)).toBe('granted')
    expect(dispatchEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: CONSENT_CHANGE_EVENT }),
    )
  })

  it('revokes immediately, aborts an in-flight flush and clears its queue', async () => {
    setConsentChoice('granted')
    let resolveFetch!: (response: { ok: boolean }) => void
    const fetchPromise = new Promise<{ ok: boolean }>((resolve) => {
      resolveFetch = resolve
    })
    const fetchMock = vi.fn().mockReturnValue(fetchPromise)
    vi.stubGlobal('fetch', fetchMock)

    const tracking = trackEvent('route_opened', {
      region_id: 'regiao-teste',
      route_id: 'rota-teste',
    })
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledOnce())
    const signal = fetchMock.mock.calls[0][1].signal as AbortSignal

    setConsentChoice('necessary')
    resolveFetch({ ok: true })
    await tracking

    expect(signal.aborted).toBe(true)
    expect(memoryStorage.getItem(QUEUE_KEY)).toBeNull()
    expect(getConsentChoice()).toBe('necessary')
  })

  it('does not let an old flush remove events queued after revocation and re-grant', async () => {
    setConsentChoice('granted')
    const oldEvent = {
      event_id: 'old-event',
      event_name: 'old',
    }
    memoryStorage.setItem(QUEUE_KEY, JSON.stringify([oldEvent]))

    let resolveOld!: (response: { ok: boolean }) => void
    const oldResponse = new Promise<{ ok: boolean }>((resolve) => {
      resolveOld = resolve
    })
    const fetchMock = vi.fn().mockReturnValueOnce(oldResponse)
    vi.stubGlobal('fetch', fetchMock)

    const oldFlush = flushEvents()
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledOnce())

    setConsentChoice('necessary')
    setConsentChoice('granted')
    const newEvent = {
      event_id: 'new-event',
      event_name: 'new',
    }
    memoryStorage.setItem(QUEUE_KEY, JSON.stringify([newEvent]))
    resolveOld({ ok: true })
    await oldFlush

    expect(JSON.parse(memoryStorage.getItem(QUEUE_KEY)!)).toEqual([newEvent])
  })

  it('stops tracking after a consent change received from another tab', async () => {
    setConsentChoice('granted')
    memoryStorage.setItem(CONSENT_KEY, 'necessary')
    window.dispatchEvent(new Event('storage'))

    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    await trackEvent('session_opened', { region_id: 'regiao-teste' })

    expect(fetchMock).not.toHaveBeenCalled()
    expect(memoryStorage.getItem(QUEUE_KEY)).toBeNull()
  })
})
