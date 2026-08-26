'use client'

import { useCallback, useEffect, useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { apiRequest } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Notice } from '@/components/ui/notice'
import { useDict, useLocale } from '@/lib/i18n/provider'
import type { CustomProvider, ProviderInfo } from '@/types'

interface CustomProviderPanelProps {
  brandId: string
  providers: ProviderInfo[]
  onChanged: () => void
}

type CustomProviderForm = {
  slug: string
  label: string
  base_url: string
  model: string
  auth_style: 'bearer' | 'x-api-key'
}

const EMPTY: CustomProviderForm = {
  slug: '',
  label: '',
  base_url: '',
  model: '',
  auth_style: 'bearer',
}

/** Derive a URL-safe identifier from the display name, so most users never
 *  have to think about the slug at all. */
function slugify(label: string): string {
  return label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40)
}

export function CustomProviderPanel({ brandId, providers, onChanged }: CustomProviderPanelProps) {
  const d = useDict()
  const { t } = useLocale()
  const [custom, setCustom] = useState<CustomProvider[]>([])
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<CustomProviderForm>({ ...EMPTY })
  const [slugTouched, setSlugTouched] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setCustom(await apiRequest<CustomProvider[]>(`/brands/${brandId}/providers/custom`))
    } catch {
      setCustom([])
    }
  }, [brandId])

  useEffect(() => {
    void load()
  }, [load])

  function updateLabel(label: string) {
    setForm((f) => ({ ...f, label, slug: slugTouched ? f.slug : slugify(label) }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await apiRequest<CustomProvider>(`/brands/${brandId}/providers/custom`, {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setForm({ ...EMPTY })
      setSlugTouched(false)
      setOpen(false)
      await load()
      onChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : d.providers.addFailed)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id: string, label: string) {
    if (!window.confirm(t(d.providers.confirmRemove, { provider: label }))) return
    setError(null)
    try {
      await apiRequest(`/brands/${brandId}/providers/custom/${id}`, { method: 'DELETE' })
      await load()
      onChanged()
    } catch (err) {
      setError(err instanceof Error ? err.message : d.providers.removeFailed)
    }
  }

  const catalogueCount = providers.filter((p) => !p.is_custom).length

  return (
    <section className="space-y-3 rounded-lg border border-border-subtle p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-[15px] font-semibold">{d.providers.customTitle}</h2>
          <p className="mt-0.5 text-[13px] text-muted-foreground">
            {t(d.providers.customDescription, { count: catalogueCount })}
          </p>
        </div>
        <Button type="button" variant="secondary" onClick={() => setOpen((v) => !v)}>
          <Plus className="h-4 w-4" />
          {open ? d.common.cancel : d.providers.addProvider}
        </Button>
      </div>

      {error && <Notice variant="danger">{error}</Notice>}

      {open && (
        <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="cp-label">{d.providers.name}</Label>
            <Input
              id="cp-label"
              value={form.label}
              onChange={(e) => updateLabel(e.target.value)}
              placeholder={d.providers.namePlaceholder}
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="cp-slug">{d.providers.identifier}</Label>
            <Input
              id="cp-slug"
              value={form.slug}
              onChange={(e) => {
                setSlugTouched(true)
                setForm((f) => ({ ...f, slug: e.target.value }))
              }}
              placeholder="my-gateway"
              pattern="[a-z0-9][a-z0-9_-]{0,38}[a-z0-9]"
              required
            />
            <p className="text-[11px] text-muted-foreground">{d.providers.identifierHint}</p>
          </div>

          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="cp-url">{d.providers.baseUrl}</Label>
            <Input
              id="cp-url"
              type="url"
              value={form.base_url}
              onChange={(e) => setForm((f) => ({ ...f, base_url: e.target.value }))}
              placeholder="https://api.example.com/v1"
              required
            />
            <p className="text-[11px] text-muted-foreground">{d.providers.baseUrlHint}</p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="cp-model">{d.providers.model}</Label>
            <Input
              id="cp-model"
              value={form.model}
              onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
              placeholder="flux-pro"
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="cp-auth">{d.providers.auth}</Label>
            <select
              id="cp-auth"
              value={form.auth_style}
              onChange={(e) =>
                setForm((f) => ({ ...f, auth_style: e.target.value as 'bearer' | 'x-api-key' }))
              }
              className="h-10 w-full rounded-md border border-input bg-background px-3 text-[13px] shadow-xs focus-visible:border-brand focus-visible:shadow-[0_0_0_3px_var(--brand-ring)] focus-visible:outline-none"
            >
              <option value="bearer">{d.providers.authBearer}</option>
              <option value="x-api-key">{d.providers.authHeader}</option>
            </select>
          </div>

          <div className="sm:col-span-2">
            <Button type="submit" disabled={saving}>
              {saving ? d.keys.adding : d.providers.addProvider}
            </Button>
          </div>
        </form>
      )}

      {custom.length > 0 && (
        <ul className="divide-y divide-border-subtle">
          {custom.map((provider) => (
            <li key={provider.id} className="flex items-center justify-between gap-3 py-2.5">
              <div className="min-w-0">
                <p className="truncate text-[14px] font-medium">{provider.label}</p>
                <p className="truncate font-mono text-[11px] text-muted-foreground">
                  {provider.slug} · {provider.base_url} · {provider.model}
                </p>
              </div>
              <Button
                type="button"
                variant="secondary"
                onClick={() => handleDelete(provider.id, provider.label)}
                aria-label={`${d.common.remove} ${provider.label}`}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
