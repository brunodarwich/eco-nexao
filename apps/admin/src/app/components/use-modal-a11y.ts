import { useEffect, useRef, type RefObject } from 'react'

const focusable =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export function useModalA11y<T extends HTMLElement>(
  open: boolean,
  onClose: () => void,
): RefObject<T | null> {
  const dialogRef = useRef<T>(null)
  const restoreRef = useRef<HTMLElement | null>(null)
  const closeRef = useRef(onClose)

  useEffect(() => {
    closeRef.current = onClose
  }, [onClose])

  useEffect(() => {
    if (!open) return
    restoreRef.current = document.activeElement as HTMLElement | null
    const dialog = dialogRef.current
    if (!dialog) return
    const getFocusable = () =>
      Array.from(dialog.querySelectorAll<HTMLElement>(focusable))
    const initial = dialog.querySelector<HTMLElement>('[data-autofocus]')
    ;(initial || getFocusable()[0] || dialog).focus()

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        closeRef.current()
        return
      }
      if (event.key !== 'Tab') return
      const items = getFocusable()
      if (!items.length) return event.preventDefault()
      if (event.shiftKey && document.activeElement === items[0]) {
        event.preventDefault()
        items.at(-1)?.focus()
      } else if (!event.shiftKey && document.activeElement === items.at(-1)) {
        event.preventDefault()
        items[0].focus()
      }
    }
    dialog.addEventListener('keydown', handleKeyDown)
    return () => {
      dialog.removeEventListener('keydown', handleKeyDown)
      restoreRef.current?.focus()
    }
  }, [open])

  return dialogRef
}
