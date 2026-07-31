import type { components } from '@econexao/contracts/api'

type ContactChannel = components['schemas']['PublicContactChannel']
type ActorLocation = components['schemas']['PublicActorLocation']

const e164Pattern = /^\+[1-9]\d{7,14}$/
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function contactHref(contact: ContactChannel) {
  const value = contact.public_value?.trim()
  if (!value) return null

  if (contact.channel_type === 'phone' && e164Pattern.test(value)) {
    return `tel:${value}`
  }
  if (contact.channel_type === 'whatsapp' && e164Pattern.test(value)) {
    return `https://wa.me/${value.slice(1)}`
  }
  if (contact.channel_type === 'email' && emailPattern.test(value)) {
    return `mailto:${value}`
  }
  if (
    contact.channel_type === 'website' ||
    contact.channel_type === 'instagram'
  ) {
    try {
      const url = new URL(value)
      return url.protocol === 'https:' || url.protocol === 'http:'
        ? url.toString()
        : null
    } catch {
      return null
    }
  }

  return null
}

export function directionsHref(location: ActorLocation) {
  const coordinates = location.point?.coordinates
  if (!coordinates || coordinates.length < 2) return null
  const [longitude, latitude] = coordinates
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) return null

  return `https://www.google.com/maps/dir/?api=1&destination=${latitude},${longitude}`
}

export function formatPublicAddress(address: unknown) {
  if (!address || typeof address !== 'object' || Array.isArray(address)) {
    return ''
  }

  const fields = address as Record<string, unknown>
  return ['street', 'address_number', 'neighborhood', 'city', 'state']
    .map((field) => fields[field])
    .filter(
      (value): value is string => typeof value === 'string' && value.length > 0,
    )
    .join(', ')
}
