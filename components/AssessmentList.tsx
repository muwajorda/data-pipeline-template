'use client'

import Link from 'next/link'
import { Button } from './Button'

interface Assessment {
  id: string
  data: any
  created_at: string
}

interface AssessmentListProps {
  assessments: Assessment[]
}

export default function AssessmentList({ assessments }: AssessmentListProps) {
  if (assessments.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-600 mb-4">No assessments yet</p>
        <Link href="/assessment">
          <Button>Create Your First Assessment</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="grid gap-4">
      {assessments.map((assessment) => (
        <div key={assessment.id} className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-lg font-semibold mb-2">
                Assessment {assessment.id.slice(0, 8)}
              </h3>
              <p className="text-sm text-gray-600">
                {new Date(assessment.created_at).toLocaleDateString()}
              </p>
              <div className="mt-2 space-x-2">
                {assessment.data?.dataType && (
                  <span className="inline-block bg-blue-100 text-blue-700 px-2 py-1 rounded text-sm">
                    {assessment.data.dataType}
                  </span>
                )}
                {assessment.data?.analysisType && (
                  <span className="inline-block bg-green-100 text-green-700 px-2 py-1 rounded text-sm">
                    {assessment.data.analysisType}
                  </span>
                )}
              </div>
            </div>
            <Link href={`/recommendations/${assessment.id}`}>
              <Button>View Results</Button>
            </Link>
          </div>
        </div>
      ))}
    </div>
  )
}
