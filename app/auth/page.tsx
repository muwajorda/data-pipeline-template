'use client'

import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function AuthPage() {
  const supabase = createClientComponentClient()
  const router = useRouter()

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === 'SIGNED_IN') {
        router.push('/dashboard')
      }
    })

    return () => subscription.unsubscribe()
  }, [router, supabase.auth])

  return (
    <div className="max-w-md mx-auto py-16 px-4">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold mb-6 text-center">Sign In</h1>
        <Auth
          supabaseClient={supabase}
          appearance={{ theme: ThemeSupa }}
          providers={['google']}
          redirectTo={`${process.env.NEXT_PUBLIC_APP_URL}/auth/callback`}
        />
      </div>
    </div>
  )
}
