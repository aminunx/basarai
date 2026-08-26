'use client'

import { createContext, useCallback, useContext, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { DEFAULT_LOCALE, LOCALE_COOKIE, type Locale } from './config'
import { getDictionary, interpolate, type Dictionary } from './index'

interface LocaleContextValue {
  locale: Locale
  dict: Dictionary
  setLocale: (locale: Locale) => void
  /** Interpolate a string from the dictionary: t(d.generator.subtitle, { brand }) */
  t: (template: string, values?: Record<string, string | number>) => string
}

const LocaleContext = createContext<LocaleContextValue | null>(null)

export function LocaleProvider({
  locale,
  children,
}: {
  locale: Locale
  children: React.ReactNode
}) {
  const router = useRouter()

  const setLocale = useCallback(
    (next: Locale) => {
      // A cookie rather than a URL segment: the locale is a preference, not a
      // different page, and this keeps every existing route untouched.
      document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`
      router.refresh()
    },
    [router],
  )

  const value = useMemo<LocaleContextValue>(() => {
    const dict = getDictionary(locale)
    return {
      locale,
      dict,
      setLocale,
      t: (template, values) => (values ? interpolate(template, values) : template),
    }
  }, [locale, setLocale])

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>
}

export function useLocale(): LocaleContextValue {
  const context = useContext(LocaleContext)
  if (!context) {
    // Rendering outside the provider is a bug, but falling back to English is
    // kinder than crashing a page over a missing wrapper.
    const dict = getDictionary(DEFAULT_LOCALE)
    return {
      locale: DEFAULT_LOCALE,
      dict,
      setLocale: () => {},
      t: (template, values) => (values ? interpolate(template, values) : template),
    }
  }
  return context
}

/** Shorthand for the common case: const d = useDict() */
export function useDict(): Dictionary {
  return useLocale().dict
}
