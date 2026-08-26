import { LanguageSwitcher } from '@/components/layout/language-switcher'

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      {/* The switcher lives in the sidebar once you are signed in — but someone
          arriving at the login screen has no sidebar and no way to change the
          language, which is exactly when they most need it. */}
      <div className="absolute end-4 top-4 z-10">
        <LanguageSwitcher compact />
      </div>
      {children}
    </>
  )
}
