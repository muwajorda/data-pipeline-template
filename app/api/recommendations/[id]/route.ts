import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = createRouteHandlerClient({ cookies })

    // Fetch assessment
    const { data: assessment, error } = await supabase
      .from('assessments')
      .select('*')
      .eq('id', params.id)
      .single()

    if (error || !assessment) {
      return NextResponse.json({ error: 'Assessment not found' }, { status: 404 })
    }

    // Check cache first
    const { data: cached } = await supabase
      .from('recommendations')
      .select('*')
      .eq('assessment_id', params.id)
      .single()

    if (cached) {
      return NextResponse.json(cached)
    }

    // Generate recommendation with OpenAI
    const prompt = `Based on this bioinformatics assessment data, provide detailed recommendations for a bioinformatics pipeline:

${JSON.stringify(assessment.data, null, 2)}

Provide recommendations in JSON format with: pipelines (array), tools (array), rationale (string), estimated_complexity (string).`

    const message = await openai.messages.create({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 1024,
      messages: [
        {
          role: 'user',
          content: prompt,
        },
      ],
    })

    const responseText =
      message.content[0].type === 'text' ? message.content[0].text : ''
    const recommendation = JSON.parse(responseText)

    // Cache recommendation
    await supabase.from('recommendations').insert([
      {
        assessment_id: params.id,
        recommendation,
        created_at: new Date().toISOString(),
      },
    ])

    return NextResponse.json({
      id: params.id,
      ...recommendation,
    })
  } catch (error) {
    console.error('Recommendation error:', error)
    return NextResponse.json(
      { error: 'Failed to generate recommendations' },
      { status: 500 }
    )
  }
}
