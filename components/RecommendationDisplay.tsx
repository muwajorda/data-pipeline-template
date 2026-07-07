'use client'

interface Recommendation {
  pipelines: string[]
  tools: string[]
  rationale: string
  estimated_complexity: string
}

interface RecommendationDisplayProps {
  recommendation: Recommendation
}

export default function RecommendationDisplay({ recommendation }: RecommendationDisplayProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-8 space-y-6">
      <section>
        <h2 className="text-2xl font-bold mb-4">Recommended Pipelines</h2>
        <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {recommendation.pipelines?.map((pipeline) => (
            <li key={pipeline} className="bg-blue-50 p-4 rounded-lg">
              <p className="font-semibold text-bio-600">{pipeline}</p>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Recommended Tools</h2>
        <ul className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {recommendation.tools?.map((tool) => (
            <li key={tool} className="bg-green-50 p-4 rounded-lg">
              <p className="font-semibold text-green-600">{tool}</p>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Rationale</h2>
        <p className="text-gray-700 leading-relaxed">{recommendation.rationale}</p>
      </section>

      <section>
        <h2 className="text-2xl font-bold mb-4">Complexity Level</h2>
        <div className="inline-block bg-purple-100 text-purple-700 px-4 py-2 rounded-lg font-semibold">
          {recommendation.estimated_complexity}
        </div>
      </section>
    </div>
  )
}
