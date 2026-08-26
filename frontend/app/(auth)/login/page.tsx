'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Eye, EyeOff, ImagePlus, KeyRound, Palette } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import { AuthShell } from '@/components/auth/auth-shell'
import { useDict } from '@/lib/i18n/provider'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export default function LoginPage() {
  const router = useRouter()
  const d = useDict()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const supabase = createClient()
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    setLoading(false)

    if (error) {
      setError(error.message)
      return
    }

    router.push('/brands')
    router.refresh()
  }

  return (
    <AuthShell
      hero={
        <>
          {d.auth.loginHeroLead}{' '}
          <em className="text-[#6FB2C0]">{d.auth.loginHeroEmphasis}</em>
        </>
      }
      subcopy={d.auth.loginSubcopy}
      features={[
        { icon: Palette, label: d.auth.loginFeature1 },
        { icon: ImagePlus, label: d.auth.loginFeature2 },
        { icon: KeyRound, label: d.auth.loginFeature3 },
      ]}
    >
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-[22px] font-semibold tracking-tight">{d.auth.loginTitle}</CardTitle>
          <CardDescription>{d.auth.loginDescription}</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="rounded-md bg-[color-mix(in_srgb,hsl(var(--destructive))_8%,white)] p-3 text-[13px] text-destructive">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">{d.auth.email}</Label>
              <Input
                id="email"
                type="email"
                placeholder={d.auth.emailPlaceholder}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">{d.auth.password}</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="pe-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute end-2 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground"
                  aria-label={showPassword ? d.auth.hidePassword : d.auth.showPassword}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" size="lg" className="w-full" disabled={loading}>
              {loading ? d.auth.loggingIn : d.auth.logIn}
            </Button>
            <p className="text-center text-[12px] text-muted-foreground">
              {d.auth.noAccount}{' '}
              <Link href="/signup" className="font-medium text-brand underline underline-offset-[2px]">
                {d.auth.signUpLink}
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </AuthShell>
  )
}
