'use client'

import { useState, type ReactNode } from 'react'
import { ProviderKey } from '@/types'
import { SegmentedControl } from '@/components/ui/segmented-control'

type Provider = 'openai' | 'gemini' | 'minimax'

interface ProviderTabsProps {
  keys: ProviderKey[]
  children: (filteredKeys: ProviderKey[], activeProvider: Provider) => ReactNode
}

export function ProviderTabs({ keys, children }: ProviderTabsProps) {
  const [activeProvider, setActiveProvider] = useState<Provider>('openai')
  const filteredKeys = keys.filter((k) => k.provider === activeProvider)
  const openaiCount = keys.filter((k) => k.provider === 'openai').length
  const geminiCount = keys.filter((k) => k.provider === 'gemini').length
  const minimaxCount = keys.filter((k) => k.provider === 'minimax').length

  return (
    <div className="space-y-4">
      <SegmentedControl
        aria-label="Provider"
        value={activeProvider}
        onChange={setActiveProvider}
        options={[
          { value: 'openai', label: `OpenAI (${openaiCount})` },
          { value: 'gemini', label: `Gemini (${geminiCount})` },
          { value: 'minimax', label: `MiniMax (${minimaxCount})` },
        ]}
      />
      {children(filteredKeys, activeProvider)}
    </div>
  )
}
