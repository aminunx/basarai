import Link from 'next/link'
import { Notice } from '@/components/ui/notice'
import { useDict, useLocale } from '@/lib/i18n/provider'

interface NoKeyNoticeProps {
  /** Display name, resolved by the caller from the provider catalogue. */
  providerLabel: string
  brandId: string
}

export function NoKeyNotice({ providerLabel, brandId }: NoKeyNoticeProps) {
  const d = useDict()
  const { t } = useLocale()
  return (
    <Notice variant="warning">
      {t(d.generator.noKeyForProvider, { provider: providerLabel })}{' '}
      <Link
        href={`/${brandId}/keys`}
        className="font-medium underline underline-offset-2"
      >
        {d.generator.addOne}
      </Link>{' '}
      {d.generator.toGenerate}
    </Notice>
  )
}
