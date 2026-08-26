'use client'

import { useEffect, useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { apiRequest } from '@/lib/api'
import { ProviderKey, type Provider, type ProviderInfo } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface AddKeyModalProps {
  brandId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  onKeyAdded: () => void
  defaultProvider?: string
  providers: ProviderInfo[]
}

export function AddKeyModal({
  brandId,
  open,
  onOpenChange,
  onKeyAdded,
  defaultProvider,
  providers,
}: AddKeyModalProps) {
  const [provider, setProvider] = useState<Provider>(defaultProvider ?? '')
  const [key, setKey] = useState('')
  const [label, setLabel] = useState('')
  const [makeActive, setMakeActive] = useState(true)
  const [showKey, setShowKey] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedProvider = providers.find((p) => p.id === provider)

  useEffect(() => {
    if (!open) return
    const known = providers.some((p) => p.id === defaultProvider)
    setProvider(known && defaultProvider ? defaultProvider : (providers[0]?.id ?? ''))
  }, [open, defaultProvider, providers])

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setKey('')
      setLabel('')
      setMakeActive(true)
      setShowKey(false)
      setError(null)
    }
    onOpenChange(newOpen)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await apiRequest<ProviderKey>(`/brands/${brandId}/keys`, {
        method: 'POST',
        body: JSON.stringify({
          provider,
          key: key.trim(),
          label: label.trim() || null,
          make_active: makeActive,
        }),
      })
      onKeyAdded()
      handleOpenChange(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add key')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-[460px]">
        <DialogHeader>
          <DialogTitle>Add API key</DialogTitle>
          <DialogDescription>
            Add a key for an image provider. It is stored securely and never shown again.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Provider</Label>
            <select
              id="add-key-provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-[13px] shadow-xs focus-visible:border-brand focus-visible:shadow-[0_0_0_3px_var(--brand-ring)] focus-visible:outline-none"
            >
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
            {selectedProvider?.key_hint && (
              <p className="font-mono text-[11px] text-muted-foreground">
                {selectedProvider.key_hint}
              </p>
            )}
            {selectedProvider?.docs_url && (
              <a
                href={selectedProvider.docs_url}
                target="_blank"
                rel="noreferrer noopener"
                className="text-[12px] underline underline-offset-2 text-muted-foreground hover:text-foreground"
              >
                Where to find this key
              </a>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="api-key">API key</Label>
            <div className="relative">
              <Input
                id="api-key"
                type={showKey ? 'text' : 'password'}
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder={provider === 'openai' ? 'sk-…' : 'AI…'}
                required
                className="pr-10 font-mono text-[13px]"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-muted-foreground hover:text-foreground"
                aria-label={showKey ? 'Hide key' : 'Show key'}
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="key-label">Label (optional)</Label>
            <Input
              id="key-label"
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g. Production key"
              maxLength={100}
            />
          </div>

          <label className="flex items-center gap-2 text-[13px]">
            <input
              type="checkbox"
              checked={makeActive}
              onChange={(e) => setMakeActive(e.target.checked)}
              className="h-4 w-4 rounded border-input accent-[var(--brand)]"
            />
            Set as active key for this provider
          </label>

          {error && <p className="text-[13px] text-destructive">{error}</p>}

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => handleOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading || !key.trim()}>
              {loading ? 'Adding…' : 'Add key'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
