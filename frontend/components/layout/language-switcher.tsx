'use client'

import { Languages } from 'lucide-react'
import { useLocale } from '@/lib/i18n/provider'
import { LOCALES, LOCALE_LABELS, type Locale } from '@/lib/i18n/config'

/**
 * Two locales today, so a segmented pair beats a dropdown — it shows the
 * alternative rather than hiding it behind a click.
 */
export function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { locale, setLocale, dict } = useLocale()

  return (
    <div className="flex items-center gap-1.5">
      {!compact && (
        <Languages className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
      )}
      <div
        role="radiogroup"
        aria-label={dict.common.language}
        className="inline-flex items-center gap-0.5 rounded-md border border-border bg-secondary p-0.5"
      >
        {LOCALES.map((option: Locale) => {
          const selected = option === locale
          return (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={selected}
              lang={option}
              onClick={() => setLocale(option)}
              className={[
                'rounded px-2 py-1 text-[12px] transition-colors',
                selected
                  ? 'bg-background font-medium text-foreground shadow-xs'
                  : 'text-muted-foreground hover:text-foreground',
              ].join(' ')}
            >
              {LOCALE_LABELS[option]}
            </button>
          )
        })}
      </div>
    </div>
  )
}
