export const LOCALES = ['en', 'ar'] as const
export type Locale = (typeof LOCALES)[number]

export const DEFAULT_LOCALE: Locale = 'en'
export const LOCALE_COOKIE = 'basar_locale'

/** Locales written right-to-left. Drives <html dir> and the RTL style layer. */
const RTL_LOCALES = new Set<Locale>(['ar'])

export function isLocale(value: unknown): value is Locale {
  return typeof value === 'string' && (LOCALES as readonly string[]).includes(value)
}

export function dirFor(locale: Locale): 'ltr' | 'rtl' {
  return RTL_LOCALES.has(locale) ? 'rtl' : 'ltr'
}

export const LOCALE_LABELS: Record<Locale, string> = {
  en: 'English',
  ar: 'العربية',
}
