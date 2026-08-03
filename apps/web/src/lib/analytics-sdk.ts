export type ConsentChoice = 'necessary' | 'granted' | null

export const CONSENT_KEY = 'econexao_consent_choice'
const ANONYMOUS_ID_KEY = 'econexao_anonymous_id'
export const QUEUE_KEY = 'econexao_analytics_queue'
export const CONSENT_CHANGE_EVENT = 'econexao:consent-change'

const activeFlushControllers = new Set<AbortController>()

const FORBIDDEN_PII = new Set([
  'name',
  'email',
  'phone',
  'cpf',
  'latitude',
  'longitude',
  'lat',
  'lng',
  'user_agent',
  'user_id',
  'ip',
  'address',
  'query',
  'text',
  'message',
  'url',
])

function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

export function getConsentChoice(): ConsentChoice {
  if (typeof window === 'undefined') return null
  const saved = localStorage.getItem(CONSENT_KEY)
  if (saved === 'necessary' || saved === 'granted') {
    return saved
  }
  return null
}

export function getAnonymousId(): string {
  if (typeof window === 'undefined') return ''
  let id = localStorage.getItem(ANONYMOUS_ID_KEY)
  if (!id) {
    id = generateUUID()
    localStorage.setItem(ANONYMOUS_ID_KEY, id)
  }
  return id
}

export function rotateAnonymousId(): string {
  if (typeof window === 'undefined') return ''
  const newId = generateUUID()
  localStorage.setItem(ANONYMOUS_ID_KEY, newId)
  return newId
}

export function clearAnalyticsQueue(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(QUEUE_KEY)
}

function notifyConsentChange(): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new Event(CONSENT_CHANGE_EVENT))
}

export function setConsentChoice(choice: 'necessary' | 'granted'): void {
  if (typeof window === 'undefined') return

  if (choice === 'necessary') {
    for (const controller of activeFlushControllers) controller.abort()
    activeFlushControllers.clear()
    clearAnalyticsQueue()
    rotateAnonymousId()
  }

  localStorage.setItem(CONSENT_KEY, choice)
  notifyConsentChange()
}

export interface AnalyticsEventPayload {
  event_id: string
  event_name: string
  schema_version: string
  occurred_at: string
  anonymous_id: string
  session_id?: string
  screen_name?: string
  region_id?: string
  route_id?: string
  properties?: Record<string, unknown>
}

export function sanitizeProperties(
  props?: Record<string, unknown>,
): Record<string, unknown> {
  if (!props) return {}
  const sanitized: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(props)) {
    if (!FORBIDDEN_PII.has(key.toLowerCase())) {
      sanitized[key] = value
    }
  }
  return sanitized
}

export async function trackEvent(
  eventName: string,
  context?: {
    screen_name?: string
    region_id?: string
    route_id?: string
    properties?: Record<string, unknown>
  },
): Promise<void> {
  if (typeof window === 'undefined') return
  const consent = getConsentChoice()
  if (consent !== 'granted') return

  const payload: AnalyticsEventPayload = {
    event_id: generateUUID(),
    event_name: eventName,
    schema_version: '1.0',
    occurred_at: new Date().toISOString(),
    anonymous_id: getAnonymousId(),
    screen_name: context?.screen_name || '',
    region_id: context?.region_id || '',
    route_id: context?.route_id || '',
    properties: sanitizeProperties(context?.properties),
  }

  if (getConsentChoice() !== 'granted') return

  const existingRaw = localStorage.getItem(QUEUE_KEY)
  const queue = readQueue(existingRaw)
  queue.push(payload)
  localStorage.setItem(QUEUE_KEY, JSON.stringify(queue.slice(-50)))

  await flushEvents()
}

function readQueue(raw: string | null): AnalyticsEventPayload[] {
  if (!raw) return []
  try {
    const parsed: unknown = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as AnalyticsEventPayload[]) : []
  } catch {
    return []
  }
}

export async function flushEvents(): Promise<void> {
  if (typeof window === 'undefined') return
  if (getConsentChoice() !== 'granted') return

  const existingRaw = localStorage.getItem(QUEUE_KEY)
  if (!existingRaw) return
  const queue = readQueue(existingRaw)
  if (queue.length === 0) return

  const controller = new AbortController()
  activeFlushControllers.add(controller)
  const sentEventIds = new Set(queue.map((event) => event.event_id))

  try {
    const res = await fetch('/api/public/events/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ events: queue }),
      signal: controller.signal,
    })
    if (res.ok && getConsentChoice() === 'granted') {
      const currentQueue = readQueue(localStorage.getItem(QUEUE_KEY))
      const remaining = currentQueue.filter(
        (event) => !sentEventIds.has(event.event_id),
      )
      if (remaining.length > 0) {
        localStorage.setItem(QUEUE_KEY, JSON.stringify(remaining))
      } else {
        clearAnalyticsQueue()
      }
    }
  } catch {
    // Manter na fila para próxima tentativa
  } finally {
    activeFlushControllers.delete(controller)
  }
}
