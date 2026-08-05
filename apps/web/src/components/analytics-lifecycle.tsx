'use client'

import { useEffect } from 'react'
import { usePathname } from 'next/navigation'
import {
  CONSENT_CHANGE_EVENT,
  getConsentChoice,
  trackEvent,
} from '../lib/analytics-sdk'

const SESSION_RECORDED_KEY = 'econexao:analytics-session-recorded'

/** Conta abertura do app, não visitantes únicos. O consentimento é validado pelo SDK. */
export function AnalyticsLifecycle() {
  const pathname = usePathname()
  useEffect(() => {
    function recordSession() {
      const regionSlug = pathname.split('/').filter(Boolean)[0]
      if (
        !regionSlug ||
        getConsentChoice() !== 'granted' ||
        sessionStorage.getItem(SESSION_RECORDED_KEY)
      ) {
        return
      }
      sessionStorage.setItem(SESSION_RECORDED_KEY, 'true')
      void trackEvent('session_opened', { region_id: regionSlug })
    }
    recordSession()
    window.addEventListener(CONSENT_CHANGE_EVENT, recordSession)
    return () => window.removeEventListener(CONSENT_CHANGE_EVENT, recordSession)
  }, [pathname])
  return null
}
