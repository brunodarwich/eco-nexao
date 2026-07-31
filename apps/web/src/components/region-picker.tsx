'use client'

import { Button } from '@econexao/ui/button'
import { FeedbackState } from '@econexao/ui/feedback-state'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { getPublishedRegions, type RegionSummary } from '@/lib/public-api'
import {
  clearRegionPreference,
  readRegionPreference,
  resolvePreferredRegion,
  saveRegionPreference,
} from '@/lib/region-preference'

type LoadState = 'loading' | 'ready' | 'error'

export function RegionPicker() {
  const router = useRouter()
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [regions, setRegions] = useState<RegionSummary[]>([])
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    getPublishedRegions(controller.signal)
      .then((publishedRegions) => {
        const searchParams = new URLSearchParams(window.location.search)
        const isReset =
          searchParams.get('trocar') === 'true' ||
          searchParams.get('reset') === 'true'

        if (isReset) {
          clearRegionPreference()
        } else {
          const preferredRegion = resolvePreferredRegion(
            publishedRegions,
            readRegionPreference(),
          )

          if (preferredRegion) {
            router.replace(`/${preferredRegion.slug}/rotas`)
            return
          }
        }

        setRegions(publishedRegions)
        setLoadState('ready')
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return
        }
        setLoadState('error')
      })

    return () => controller.abort()
  }, [reloadKey, router])

  function rememberRegion(slug: string) {
    saveRegionPreference(slug)
  }

  function retry() {
    setLoadState('loading')
    setReloadKey((key) => key + 1)
  }

  if (loadState === 'loading') {
    return (
      <FeedbackState
        message="Estamos consultando as regiões disponíveis."
        title="Carregando regiões"
        variant="loading"
      />
    )
  }

  if (loadState === 'error') {
    return (
      <FeedbackState
        action={<Button onClick={retry}>Tentar novamente</Button>}
        message="Verifique sua conexão e tente novamente."
        title="Não foi possível carregar as regiões"
        variant="error"
      />
    )
  }

  if (regions.length === 0) {
    return (
      <FeedbackState
        message="Ainda não há territórios publicados. Volte em breve."
        title="Nenhuma região disponível"
        variant="empty"
      />
    )
  }

  return (
    <ul aria-label="Regiões disponíveis" className="region-grid">
      {regions.map((region) => (
        <li className="region-card" key={region.id}>
          <div>
            <h2>{region.public_name}</h2>
            <p>
              {region.short_description || 'Explore as rotas deste território.'}
            </p>
          </div>
          <Link
            className="ui-button region-card__action"
            href={`/${region.slug}/rotas`}
            onClick={() => rememberRegion(region.slug)}
          >
            Explorar esta região
          </Link>
        </li>
      ))}
    </ul>
  )
}
