'use client'

import { useEffect, useState } from 'react'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import { useRouter } from 'next/navigation'
import AssessmentList from '@/components/AssessmentList'
import { Button } from '@/components/Button'
import Link from 'next/link'

export default function DashboardPage() {
  const supabase = createClientComponentClient()
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [assessments, setAssessments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const getUser = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        router.push('/auth')
        return
      }
      setUser(session.user)
      fetchAssessments(session.user.id)
    }

    getUser()
  }, [router, supabase.auth])

  const fetchAssessments = async (userId: string) => {
    try {
      const response = await fetch(`/api/assessments?userId=${userId}`)
      if (response.ok) {
        const data = await response.json()
        setAssessments(data)
      }
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="max-w-6xl mx-auto py-12 px-4">Loading...</div>
  }

  return (
    <div className="max-w-6xl mx-auto py-12 px-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">Dashboard</h1>
        <Link href="/assessment">
          <Button>
            New Assessment
          </Button>
        </Link>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <div className="bg-blue-50 p-6 rounded-lg">
          <p className="text-sm text-gray-600 mb-2">Total Assessments</p>
          <p className="text-3xl font-bold text-blue-600">{assessments.length}</p>
        </div>
        <div className="bg-green-50 p-6 rounded-lg">
          <p className="text-sm text-gray-600 mb-2">Last Assessment</p>
          <p className="text-lg font-semibold">
            {assessments[0]?.created_at
              ? new Date(assessments[0].created_at).toLocaleDateString()
              : 'None yet'}
          </p>
        </div>
        <div className="bg-purple-50 p-6 rounded-lg">
          <p className="text-sm text-gray-600 mb-2">User</p>
          <p className="text-lg font-semibold">{user?.email}</p>
        </div>
      </div>

      <h2 className="text-2xl font-bold mb-4">Your Assessments</h2>
      <AssessmentList assessments={assessments} />
    </div>
  )
}
