'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import AssessmentForm from '@/components/AssessmentForm'
import { Button } from '@/components/Button'

export default function AssessmentPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (formData: any) => {
    setLoading(true)
    try {
      const response = await fetch('/api/assessment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      if (!response.ok) throw new Error('Assessment failed')

      const { assessmentId } = await response.json()
      router.push(`/recommendations/${assessmentId}`)
    } catch (error) {
      console.error('Error submitting assessment:', error)
      alert('Failed to submit assessment. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <h1 className="text-4xl font-bold mb-2">Bioinformatics Assessment</h1>
      <p className="text-gray-600 mb-8">
        Answer a few questions to help us understand your bioinformatics pipeline needs
      </p>
      <AssessmentForm onSubmit={handleSubmit} loading={loading} />
    </div>
  )
}
