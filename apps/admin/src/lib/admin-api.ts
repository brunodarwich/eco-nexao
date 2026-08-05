'use client'

import type { components } from '@econexao/contracts/api'

export type AdminRequestError =
  'unauthorized' | 'forbidden' | 'rate-limited' | 'server-error' | 'unavailable'

interface AdminErrorPayload {
  code?: string
  detail?: string
  field_errors?: Record<string, string[]>
  message?: string
}

export class AdminApiError extends Error {
  constructor(
    message: string,
    public readonly kind: AdminRequestError,
    public readonly status: number,
  ) {
    super(message)
    this.name = 'AdminApiError'
  }
}

export function classifyAdminResponse(status: number): AdminRequestError {
  if (status === 401) return 'unauthorized'
  if (status === 403) return 'forbidden'
  if (status === 429) return 'rate-limited'
  if (status >= 500) return 'server-error'
  return 'unavailable'
}

function requestPath(path: string) {
  return `/api/admin/${path.replace(/^\/+/, '')}`
}

async function readJson(response: Response): Promise<unknown> {
  return response.json().catch(() => null)
}

function payloadMessage(payload: unknown, fallback: string) {
  if (!payload || typeof payload !== 'object') return fallback
  const error = payload as AdminErrorPayload
  const fieldMessage = Object.values(error.field_errors ?? {}).flat()[0]
  return error.message || error.detail || fieldMessage || fallback
}

export function getAdminRequestError(error: unknown): AdminRequestError {
  return error instanceof AdminApiError ? error.kind : 'unavailable'
}

export function getAdminErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback
}

export async function adminRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  let response: Response
  try {
    response = await fetch(requestPath(path), {
      cache: 'no-store',
      credentials: 'include',
      ...init,
    })
  } catch {
    throw new AdminApiError(
      'Não foi possível alcançar o serviço administrativo.',
      'unavailable',
      0,
    )
  }

  const payload = await readJson(response)
  if (!response.ok) {
    throw new AdminApiError(
      payloadMessage(
        payload,
        'A operação administrativa não pôde ser concluída.',
      ),
      classifyAdminResponse(response.status),
      response.status,
    )
  }

  return payload as T
}

export async function adminMutation<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const csrf = await adminRequest<{ csrf_token?: string }>('auth/csrf')
  if (!csrf.csrf_token) {
    throw new AdminApiError(
      'Não foi possível iniciar a sessão segura.',
      'unavailable',
      0,
    )
  }

  const headers = new Headers(init.headers)
  headers.set('X-CSRFToken', csrf.csrf_token)
  return adminRequest<T>(path, { ...init, headers })
}

export type DashboardSummaryApi = components['schemas']['DashboardSummary']

export async function fetchDashboardSummary(
  regionSlug?: string,
): Promise<DashboardSummaryApi> {
  const query = regionSlug
    ? `?region_slug=${encodeURIComponent(regionSlug)}`
    : ''
  return adminRequest<DashboardSummaryApi>(`dashboard/summary${query}`)
}
