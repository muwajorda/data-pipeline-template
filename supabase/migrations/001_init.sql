-- Create auth schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS auth;

-- Assessments table
CREATE TABLE IF NOT EXISTS public.assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  data JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CONSTRAINT user_fk FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Recommendations table
CREATE TABLE IF NOT EXISTS public.recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL,
  recommendation JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  CONSTRAINT assessment_fk FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_assessments_user_id ON public.assessments(user_id);
CREATE INDEX idx_assessments_created_at ON public.assessments(created_at);
CREATE INDEX idx_recommendations_assessment_id ON public.recommendations(assessment_id);

-- Row Level Security
ALTER TABLE public.assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can view their own assessments"
  ON public.assessments FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own assessments"
  ON public.assessments FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view recommendations for their assessments"
  ON public.recommendations FOR SELECT
  USING (
    assessment_id IN (
      SELECT id FROM assessments WHERE user_id = auth.uid()
    )
  );
