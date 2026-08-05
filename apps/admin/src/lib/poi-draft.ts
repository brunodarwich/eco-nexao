'use client'

import { adminMutation } from './admin-api'

export interface PoiDraftInput {
  actorId: string
  address: string
  category: string
  displayName: string
  phone: string
  regionId: string
}

export interface EditorialRevisionResponse {
  snapshot?: { status?: string }
  target_id: string
}

export function savePoiDraft(input: PoiDraftInput) {
  return adminMutation<EditorialRevisionResponse>('editorial/revisions', {
    body: JSON.stringify({
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
    }),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  })
}
