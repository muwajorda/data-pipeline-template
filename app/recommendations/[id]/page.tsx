'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import RecommendationDisplay from '@/components/RecommendationDisplay'
import { Button } from '@/components/Button'

export default function RecommendationsPage() {
  const params = useParams()
  const assessmentId = params.id as string
  const [recommendation, setRecommendation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchRecommendation = async () => {
      try {
        const response = await fetch(`/api/recommendations/${assessmentId}`)
        if (!response.ok) throw new Error('Failed to fetch recommendation')
        const data = await response.json()
        setRecommendation(data)
      } catch (err) {
        setError('Failed to load recommendations')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchRecommendation()
  }, [assessmentId])

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 text-center">
        <p className="text-lg text-gray-600">Generating recommendations...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4">
        <p className="text-lg text-red-600">{error}</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto py-12 px-4">
      <h1 className="text-4xl font-bold mb-8">Your Recommendations</h1>
      {recommendation && (
        <>
          <RecommendationDisplay recommendation={recommendation} />
          <div className="mt-8 flex gap-4">
            <a href={`/api/project/download/${assessmentId}`}>
              <Button>
                Download Project
              </Button>
            </a>
            <a href="/dashboard">
              <Button variant="outline">
                View Dashboard
              </Button>
            </a>
          </div>
        </>
      )}
    </div>
  )
}
