import type { MetadataRoute } from 'next'

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'ECOnexão',
    short_name: 'ECOnexão',
    description: 'Rotas confiáveis e conexões locais para descobrir destinos.',
    start_url: '/',
    display: 'standalone',
    background_color: '#F7F8F5',
    theme_color: '#33601E',
    lang: 'pt-BR',
  }
}
