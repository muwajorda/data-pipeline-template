import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'
import JSZip from 'jszip'
import { generateProjectFiles } from '@/lib/projectGenerator'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const supabase = createRouteHandlerClient({ cookies })

    const { data: assessment, error: assessmentError } = await supabase
      .from('assessments')
      .select('*')
      .eq('id', params.id)
      .single()

    if (assessmentError || !assessment) {
      return NextResponse.json(
        { error: 'Assessment not found' },
        { status: 404 }
      )
    }

    const { data: recommendation, error: recError } = await supabase
      .from('recommendations')
      .select('*')
      .eq('assessment_id', params.id)
      .single()

    if (recError || !recommendation) {
      return NextResponse.json(
        { error: 'Recommendation not found' },
        { status: 404 }
      )
    }

    // Generate project files
    const files = generateProjectFiles(assessment.data, recommendation.recommendation)

    // Create ZIP
    const zip = new JSZip()
    Object.entries(files).forEach(([path, content]) => {
      zip.file(path, content as string)
    })

    const zipBuffer = await zip.generateAsync({ type: 'arraybuffer' })

    return new NextResponse(zipBuffer, {
      headers: {
        'Content-Type': 'application/zip',
        'Content-Disposition': 'attachment; filename=bioinformatics-project.zip',
      },
    })
  } catch (error) {
    console.error('Download error:', error)
    return NextResponse.json(
      { error: 'Failed to generate project' },
      { status: 500 }
    )
  }
}
