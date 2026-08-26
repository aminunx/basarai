'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '@/lib/api'
import type { ProviderKey } from '@/types'

/** Which providers this brand currently has an active key for, keyed by id. */
export type ActiveKeys = Record<string, boolean>

interface UseActiveKeysResult {
  activeKeys: ActiveKeys
  hasActiveKey: (provider: string) => boolean
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useActiveKeys(brandId: string): UseActiveKeysResult {
  const [activeKeys, setActiveKeys] = useState<ActiveKeys>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const keys = await apiRequest<ProviderKey[]>(`/brands/${brandId}/keys`)
      const map: ActiveKeys = {}
      for (const key of keys) {
        if (key.is_active) map[key.provider] = true
      }
      setActiveKeys(map)
    } catch (err) {
      setActiveKeys({})
      setError(err instanceof Error ? err.message : 'Failed to load keys')
    } finally {
      setLoading(false)
    }
  }, [brandId])

  useEffect(() => {
    void load()
  }, [load])

  const hasActiveKey = useCallback(
    (provider: string) => Boolean(activeKeys[provider]),
    [activeKeys],
  )

  return { activeKeys, hasActiveKey, loading, error, refetch: load }
}
