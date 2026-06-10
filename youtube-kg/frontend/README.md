# YouTube Creator Knowledge Graph - Frontend

A Next.js frontend for the YouTube Creator Knowledge Graph application.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Auth**: Supabase Authentication
- **Hosting**: Vercel
- **API Client**: Fetch API

## Features

- User authentication (sign up/sign in)
- Project management (create, list, view)
- Integration with FastAPI backend
- Real-time updates via Supabase

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Supabase account
- Vercel account (for deployment)

### Local Development

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up environment variables**:
   Copy `.env.example` to `.env.local` and fill in:
   - `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Your Supabase anon key
   - `NEXT_PUBLIC_API_URL` - Your FastAPI backend URL

3. **Run the development server**:
   ```bash
   npm run dev
   ```

4. **Open browser**:
   Visit http://localhost:3000

## Getting Supabase Credentials

1. Go to https://app.supabase.com/projects
2. Select your project
3. Go to Settings → API
4. Copy the "URL" (use this for `NEXT_PUBLIC_SUPABASE_URL`)
5. Copy the "anon public" key (use this for `NEXT_PUBLIC_SUPABASE_ANON_KEY`)

## Deploying to Vercel

### Option 1: Using Vercel CLI

```bash
npm install -g vercel
vercel
```

### Option 2: Using GitHub

1. Push code to GitHub
2. Go to https://vercel.com
3. Click "New Project"
4. Select your GitHub repository
5. Set environment variables
6. Click "Deploy"

### Environment Variables on Vercel

Add these in Vercel project settings:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL`

## Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Root (redirects to auth or dashboard)
│   ├── layout.tsx            # Root layout
│   ├── auth/
│   │   └── page.tsx          # Login/signup page
│   ├── dashboard/
│   │   └── page.tsx          # Projects list
│   └── projects/
│       └── new/
│           └── page.tsx      # Create project page
├── lib/
│   ├── supabase.ts           # Supabase client
│   └── api.ts                # FastAPI client
├── .env.local                # Local environment variables
└── vercel.json               # Vercel configuration
```

## Development Workflow

1. Make changes to components/pages
2. Hot reload updates automatically
3. Test locally before deploying

## API Integration

The frontend connects to the FastAPI backend at `NEXT_PUBLIC_API_URL`:

- `POST /api/v1/auth/register` - Register user
- `GET /api/v1/projects` - List user's projects
- `POST /api/v1/projects` - Create new project
- `GET /api/v1/projects/{id}` - Get project details

## Authentication Flow

1. User signs up/logs in with Supabase
2. JWT token stored in browser
3. Token sent in Authorization header for API calls
4. Backend validates token and returns user data

## Next Steps

- [ ] Get Supabase anon key
- [ ] Update `.env.local`
- [ ] Run locally: `npm run dev`
- [ ] Deploy to Vercel
- [ ] Test auth flow
- [ ] Create sample project
- [ ] View knowledge graph
