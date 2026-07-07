'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Button } from './Button'

interface AssessmentFormProps {
  onSubmit: (data: any) => Promise<void>
  loading: boolean
}

export default function AssessmentForm({ onSubmit, loading }: AssessmentFormProps) {
  const { register, handleSubmit } = useForm()

  const questions = [
    {
      name: 'dataType',
      label: 'What type of sequencing data will you work with?',
      options: ['RNA-seq', 'WES', 'ChIP-seq', 'ATAC-seq', 'Multiple'],
    },
    {
      name: 'analysisType',
      label: 'What is your primary analysis goal?',
      options: [
        'Differential expression',
        'Variant calling',
        'Peak calling',
        'Comparative analysis',
        'Custom analysis',
      ],
    },
    {
      name: 'experience',
      label: 'Your bioinformatics experience level',
      options: ['Beginner', 'Intermediate', 'Advanced'],
    },
    {
      name: 'teamSize',
      label: 'Team size',
      options: ['Solo', 'Small (2-5)', 'Medium (6-10)', 'Large (10+)'],
    },
    {
      name: 'deploymentMethod',
      label: 'How will you deploy this pipeline?',
      options: ['Local machine', 'HPC cluster', 'Cloud (AWS/GCP)', 'Container'],
    },
  ]

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="bg-white rounded-lg shadow-lg p-8 space-y-8">
      {questions.map((q) => (
        <div key={q.name}>
          <label className="block text-lg font-semibold mb-4 text-gray-900">
            {q.label}
          </label>
          <div className="space-y-2">
            {q.options.map((option) => (
              <label key={option} className="flex items-center">
                <input
                  type="radio"
                  value={option}
                  {...register(q.name, { required: true })}
                  className="w-4 h-4 text-bio-600"
                />
                <span className="ml-3 text-gray-700">{option}</span>
              </label>
            ))}
          </div>
        </div>
      ))}

      <Button
        type="submit"
        disabled={loading}
        className="w-full text-lg py-3"
      >
        {loading ? 'Generating Recommendations...' : 'Get Recommendations'}
      </Button>
    </form>
  )
}
