import Link from 'next/link'
import { Button } from '@/components/Button'

export default function Home() {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen">
      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 py-20 text-center">
        <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
          Build Your Bioinformatics Pipeline
        </h1>
        <p className="text-xl text-gray-700 mb-8 max-w-2xl mx-auto">
          Get AI-powered recommendations and generate a starter bioinformatics project tailored to your needs.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/assessment">
            <Button size="lg">
              Start Assessment
            </Button>
          </Link>
          <Link href="/auth">
            <Button variant="outline" size="lg">
              Sign In
            </Button>
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="bg-white p-8 rounded-lg shadow-md">
            <div className="text-4xl mb-4">📋</div>
            <h3 className="text-xl font-bold mb-2">Assessment</h3>
            <p className="text-gray-600">
              Answer a tailored questionnaire about your bioinformatics needs
            </p>
          </div>
          <div className="bg-white p-8 rounded-lg shadow-md">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-xl font-bold mb-2">AI Recommendations</h3>
            <p className="text-gray-600">
              Get personalized pipeline recommendations powered by OpenAI
            </p>
          </div>
          <div className="bg-white p-8 rounded-lg shadow-md">
            <div className="text-4xl mb-4">📦</div>
            <h3 className="text-xl font-bold mb-2">Project Generation</h3>
            <p className="text-gray-600">
              Download a ready-to-use bioinformatics project with Nextflow pipelines
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
