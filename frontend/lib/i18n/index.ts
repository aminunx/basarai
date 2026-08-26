import { ar } from './dictionaries/ar'
import { en, type Dictionary } from './dictionaries/en'
import { DEFAULT_LOCALE, type Locale } from './config'

const DICTIONARIES: Record<Locale, Dictionary> = { en, ar }

export function getDictionary(locale: Locale): Dictionary {
  return DICTIONARIES[locale] ?? DICTIONARIES[DEFAULT_LOCALE]
}

/**
 * Substitute {name} placeholders. Kept deliberately small — the app needs
 * interpolation, not a full ICU message format, and a dependency here would
 * be paid for on every page load.
 */
export function interpolate(template: string, values: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key: string) =>
    key in values ? String(values[key]) : match,
  )
}

export type { Dictionary }
export * from './config'
