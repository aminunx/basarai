import Link from 'next/link'
import { Notice } from '@/components/ui/notice'

interface NoKeyNoticeProps {
  /** Display name, resolved by the caller from the provider catalogue. */
  providerLabel: string
  brandId: string
}

export function NoKeyNotice({ providerLabel, brandId }: NoKeyNoticeProps) {
  return (
    <Notice variant="warning">
      No {providerLabel} key yet —{' '}
      <Link
        href={`/${brandId}/keys`}
        className="font-medium underline underline-offset-2"
      >
        Add one
      </Link>{' '}
      to generate with this provider.
    </Notice>
  )
}
