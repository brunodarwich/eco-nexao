/* eslint-disable @next/next/no-img-element */
import { describe, expect, it, vi } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { FeedbackState } from '@econexao/ui/feedback-state'
import { GooglePlacesPreviewSection } from './discovery-workspace'
import AdminHomePage from './page'

interface MockImgProps extends Omit<
  React.ImgHTMLAttributes<HTMLImageElement>,
  'src'
> {
  src?: string | { src: string }
}

vi.mock('next/image', () => ({
  default: (props: MockImgProps) => (
    <img
      alt={props.alt}
      className={props.className}
      src={typeof props.src === 'string' ? props.src : props.src?.src || ''}
    />
  ),
}))

describe('shared feedback states', () => {
  it('announces errors and their recovery message', () => {
    const markup = renderToStaticMarkup(
      <FeedbackState
        message="Tente novamente."
        title="Falha ao carregar"
        variant="error"
      />,
    )

    expect(markup).toContain('role="alert"')
    expect(markup).toContain('Falha ao carregar')
    expect(markup).toContain('Tente novamente.')
  })
})

describe('Google Places preview', () => {
  it('keeps provider attribution and human verification visible', () => {
    const markup = renderToStaticMarkup(
      <GooglePlacesPreviewSection
        preview={{
          attribution: 'Google Maps',
          candidates: [
            {
              display_name: 'Candidato temporário',
              formatted_address: 'Endereço temporário',
              google_maps_uri: 'https://maps.google.com/?cid=123',
              latitude: -2.56,
              longitude: -54.97,
              place_id: 'place-123',
              primary_type: 'restaurant',
            },
          ],
          result_count: 1,
          run_id: 'run-123',
        }}
      />,
    )

    expect(markup).toContain('Conteúdo fornecido por')
    expect(markup).toContain('aria-label="Google Maps"')
    expect(markup).toContain('não foram importados')
    expect(markup).toContain('Candidato temporário')
    expect(markup).toContain('rel="noreferrer"')
    expect(markup).not.toContain('maplibre')
  })
})

describe('AdminHomePage Component', () => {
  it('renders page header, title, and operational dashboard', () => {
    const markup = renderToStaticMarkup(<AdminHomePage />)

    expect(markup).toContain('Painel Operacional')
    expect(markup).toContain('Operação Editorial &amp; Reflexo do App')
    expect(markup).toContain(
      'Acompanhe os acessos ao aplicativo, o engajamento nos pontos da rota',
    )
    expect(markup).toContain('operational-dashboard')
  })
})
