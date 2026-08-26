import { cookies } from 'next/headers'
import { DEFAULT_LOCALE, LOCALE_COOKIE, isLocale, type Locale } from './config'

/** Read the locale preference on the server, for <html lang> and <html dir>. */
export function getServerLocale(): Locale {
  const value = cookies().get(LOCALE_COOKIE)?.value
  return isLocale(value) ? value : DEFAULT_LOCALE
}
