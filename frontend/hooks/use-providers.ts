'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiRequest } from '@/lib/api'
import type { ProviderInfo } from '@/types'

interface UseProvidersResult {
  providers: ProviderInfo[]
  byId: Record<string, ProviderInfo>
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

/**
 * The provider list is no longer a constant — it is the built-in catalogue plus
 * whatever endpoints this brand has registered, so it has to be fetched.
 */
export function useProviders(brandId: string): UseProvidersResult {
  const [providers, setProviders] = useState<ProviderInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setProviders(await apiRequest<ProviderInfo[]>(`/brands/${brandId}/providers`))
    } catch (err) {
      setProviders([])
      setError(err instanceof Error ? err.message : 'Failed to load providers')
    } finally {
      setLoading(false)
    }
  }, [brandId])

  useEffect(() => {
    void load()
  }, [load])

  const byId = Object.fromEntries(providers.map((p) => [p.id, p]))
  return { providers, byId, loading, error, refetch: load }
}
