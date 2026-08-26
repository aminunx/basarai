'use client'

import type { Provider, ProviderInfo } from '@/types'
import type { ActiveKeys } from '@/hooks/use-active-keys'
import { NoKeyNotice } from '@/components/generation/no-key-notice'
import { Eyebrow } from '@/components/ui/eyebrow'
import { SegmentedControl } from '@/components/ui/segmented-control'
import { useDict } from '@/lib/i18n/provider'

interface ProviderSelectorProps {
  value: Provider
  onChange: (value: Provider) => void
  providers: ProviderInfo[]
  activeKeys: ActiveKeys
  brandId: string
  disabled?: boolean
}

// Beyond a handful of choices a segmented control stops being scannable, so the
// UI switches to a dropdown. The list is open-ended now, so this will happen.
const SEGMENTED_LIMIT = 3

export function ProviderSelector({
  value, onChange, providers, activeKeys, brandId, disabled,
}: ProviderSelectorProps) {
  const d = useDict()
  const current = providers.find((p) => p.id === value)
  const currentHasKey = Boolean(activeKeys[value])

  const label = (provider: ProviderInfo) =>
    activeKeys[provider.id] ? provider.label : `${provider.label} — ${d.keys.unchecked}`

  return (
    <div className="flex flex-col gap-2">
      <Eyebrow>{d.generator.provider}</Eyebrow>

      {providers.length <= SEGMENTED_LIMIT ? (
        <SegmentedControl
          aria-label={d.generator.provider}
          value={value}
          onChange={onChange}
          disabled={disabled}
          options={providers.map((p) => ({ value: p.id, label: p.label }))}
        />
      ) : (
        <>
          <label htmlFor="provider-select" className="sr-only">
            {d.generator.provider}
          </label>
          <select
            id="provider-select"
            value={value}
            disabled={disabled}
            onChange={(e) => onChange(e.target.value)}
            className="h-10 rounded-md border border-input bg-background px-3 text-[13px] shadow-xs focus-visible:border-brand focus-visible:shadow-[0_0_0_3px_var(--brand-ring)] focus-visible:outline-none disabled:opacity-50"
          >
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {label(p)}
              </option>
            ))}
          </select>
        </>
      )}

      {current && (
        <p className="font-mono text-[11px] text-muted-foreground">{current.default_model}</p>
      )}
      {!currentHasKey && (
        <NoKeyNotice providerLabel={current?.label ?? value} brandId={brandId} />
      )}
    </div>
  )
}
