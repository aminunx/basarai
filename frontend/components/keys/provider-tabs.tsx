'use client'

import { useEffect, useState, type ReactNode } from 'react'
import { useDict } from '@/lib/i18n/provider'
import type { Provider, ProviderInfo, ProviderKey } from '@/types'

interface ProviderTabsProps {
  keys: ProviderKey[]
  providers: ProviderInfo[]
  children: (filteredKeys: ProviderKey[], activeProvider: Provider) => ReactNode
}

/**
 * A tab per provider. The list is open-ended, so these wrap rather than sitting
 * in a fixed segmented control.
 */
export function ProviderTabs({ keys, providers, children }: ProviderTabsProps) {
  const d = useDict()
  const [activeProvider, setActiveProvider] = useState<Provider>(providers[0]?.id ?? 'openai')

  // The catalogue arrives asynchronously, and a custom provider can be removed
  // while its tab is selected.
  useEffect(() => {
    if (providers.length === 0) return
    if (!providers.some((p) => p.id === activeProvider)) {
      setActiveProvider(providers[0].id)
    }
  }, [providers, activeProvider])

  const filteredKeys = keys.filter((k) => k.provider === activeProvider)

  return (
    <div className="space-y-4">
      <div role="tablist" aria-label={d.generator.provider} className="flex flex-wrap gap-1.5">
        {providers.map((provider) => {
          const count = keys.filter((k) => k.provider === provider.id).length
          const selected = provider.id === activeProvider
          return (
            <button
              key={provider.id}
              type="button"
              role="tab"
              aria-selected={selected}
              onClick={() => setActiveProvider(provider.id)}
              className={[
                'h-9 rounded-md border px-3 text-[13px] transition-colors',
                selected
                  ? 'border-brand bg-secondary font-medium text-foreground'
                  : 'border-border text-muted-foreground hover:text-foreground',
              ].join(' ')}
            >
              {provider.label} ({count})
              {provider.is_custom && (
                <span className="ms-1.5 font-mono text-[10px] opacity-60">
                  {d.providers.custom}
                </span>
              )}
            </button>
          )
        })}
      </div>
      {children(filteredKeys, activeProvider)}
    </div>
  )
}
