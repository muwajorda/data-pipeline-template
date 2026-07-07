'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import { useRouter } from 'next/navigation'
import { Button } from './Button'

export default function Navbar() {
  const supabase = createClientComponentClient()
  const router = useRouter()
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const getUser = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      setUser(session?.user ?? null)
    }

    getUser()

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setUser(session?.user ?? null)
      }
    )

    return () => subscription?.unsubscribe()
  }, [supabase.auth])

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    router.push('/')
  }

  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold text-bio-600">
          🧬 BioGen
        </Link>

        <div className="flex gap-4 items-center">
          {user ? (
            <>
              <Link href="/dashboard">
                <Button variant="ghost">Dashboard</Button>
              </Link>
              <button
                onClick={handleSignOut}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
              >
                Sign Out
              </button>
            </>
          ) : (
            <>
              <Link href="/auth">
                <Button variant="ghost">Sign In</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
