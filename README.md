# Bioinformatics Project Generator

An AI-powered web application that helps researchers generate starter bioinformatics pipelines tailored to their needs.

## Features

✅ **User Authentication**: Sign in with Google via Supabase  
✅ **Assessment Questionnaire**: Answer questions about your pipeline needs  
✅ **AI Recommendations**: Get personalized pipeline recommendations powered by OpenAI  
✅ **Project Generation**: Download a ready-to-use Nextflow project  
✅ **Dashboard**: Save and manage multiple assessments  
✅ **PDF Reports**: Export recommendations as PDF  

## Tech Stack

- **Frontend**: Next.js 14, React, Tailwind CSS
- **Backend**: Next.js API routes
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth with Google OAuth
- **AI**: OpenAI API for recommendations
- **Deployment**: Vercel

## Getting Started

### Prerequisites

- Node.js 18+
- Supabase account
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/muwajorda/data-pipeline-template.git
cd web-app
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.local.example .env.local
```

Fill in your Supabase and OpenAI credentials.

4. Run the development server:
```bash
npm run dev
```

Visit http://localhost:3000

## Database Setup

Create these tables in Supabase:

### assessments
```sql
CREATE TABLE assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  data JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### recommendations
```sql
CREATE TABLE recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  recommendation JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## MVP Goals (Version 1)

- [x] User sign-in flow
- [x] Assessment questionnaire
- [x] AI-powered recommendations
- [x] Bioinformatics project generation
- [x] Project download as ZIP
- [ ] PDF report export
- [ ] User dashboard with assessment history
- [ ] Sharing recommendations with team members

## Deployment

Deploy to Vercel:

```bash
npm install -g vercel
vercel
```

Add environment variables in Vercel dashboard and your app is live!

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT
