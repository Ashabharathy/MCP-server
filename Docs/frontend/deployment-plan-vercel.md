# Frontend Deployment Plan — Vercel

## Overview

This document provides a step-by-step guide to deploy the GROWW Weekly Review Pulse Agent Dashboard (Next.js frontend) to Vercel.

---

## Prerequisites

- Node.js 18+ installed locally
- Git installed and configured
- Vercel account (free tier available)
- GitHub account (for Vercel integration)
- Backend API endpoints available (or mock data for initial deployment)

---

## Step 1: Initialize Next.js Project

If you haven't already created the Next.js frontend:

```bash
# Navigate to your project directory
cd a:\NEXTLEAP\MCP

# Create Next.js app
npx create-next-app@latest frontend --typescript --tailwind --eslint

# Navigate to the frontend directory
cd frontend
```

**Configuration options:**
- TypeScript: Yes
- ESLint: Yes
- Tailwind CSS: Yes
- App Router: Yes (recommended)
- Import alias: `@/*`

---

## Step 2: Project Structure Setup

Organize your frontend project structure:

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Dashboard home
│   ├── runs/
│   │   ├── [id]/page.tsx   # Run details page
│   │   └── page.tsx        # Runs list
│   ├── pulse/
│   │   └── page.tsx        # Pulse viewer
│   ├── config/
│   │   └── page.tsx        # Configuration panel
│   ├── alerts/
│   │   └── page.tsx        # Alerts & notifications
│   └── analytics/
│       └── page.tsx        # Analytics & trends
├── components/
│   ├── ui/                 # Reusable UI components
│   ├── layout/             # Layout components (Header, Sidebar, etc.)
│   └── dashboard/          # Dashboard-specific components
├── lib/
│   ├── api.ts              # API client functions
│   └── utils.ts            # Utility functions
├── types/
│   └── index.ts            # TypeScript type definitions
├── public/                 # Static assets
├── .env.local              # Local environment variables
├── .env.example            # Example environment variables
├── next.config.js          # Next.js configuration
├── tailwind.config.ts      # Tailwind CSS configuration
└── package.json            # Dependencies
```

---

## Step 3: Install Dependencies

Install additional dependencies for the dashboard:

```bash
# UI components library (optional but recommended)
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tabs

# Chart library for analytics
npm install recharts

# Date handling
npm install date-fns

# HTTP client
npm install axios

# Icons
npm install lucide-react

# Form handling
npm install react-hook-form zod @hookform/resolvers
```

---

## Step 4: Configure Environment Variables

Create `.env.local` for local development:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Authentication (if needed)
NEXT_PUBLIC_API_KEY=your_api_key_here

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_ALERTS=true
```

Create `.env.example` for reference:

```env
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_API_KEY=
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_ALERTS=true
```

---

## Step 5: Set Up Vercel Environment Variables

1. **Push code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/your-username/groww-pulse-dashboard.git
   git push -u origin main
   ```

2. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Sign in with GitHub
   - Click "Add New Project"
   - Import your GitHub repository

3. **Configure Project Settings:**
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend` (if frontend is in a subdirectory)
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `.next` (default)

4. **Add Environment Variables in Vercel:**
   - Go to Settings → Environment Variables
   - Add the same variables from `.env.example`
   - For production, use production API URLs and keys

---

## Step 6: Configure Next.js for Vercel

Update `next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Environment variables available on the client side
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_API_KEY: process.env.NEXT_PUBLIC_API_KEY,
    NEXT_PUBLIC_ENABLE_ANALYTICS: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS,
    NEXT_PUBLIC_ENABLE_ALERTS: process.env.NEXT_PUBLIC_ENABLE_ALERTS,
  },
  
  // Optimize images
  images: {
    domains: ['your-domain.com'],
  },
  
  // API rewrites (if backend is on different domain)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL + '/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
```

---

## Step 7: Create API Client

Create `lib/api.ts`:

```typescript
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth header if needed
if (process.env.NEXT_PUBLIC_API_KEY) {
  api.defaults.headers.common['Authorization'] = `Bearer ${process.env.NEXT_PUBLIC_API_KEY}`;
}

export default api;

// API functions
export const api = {
  // Pipeline runs
  getRuns: async () => {
    const response = await api.get('/runs');
    return response.data;
  },
  
  getRun: async (id: string) => {
    const response = await api.get(`/runs/${id}`);
    return response.data;
  },
  
  triggerRun: async (config: any) => {
    const response = await api.post('/runs', config);
    return response.data;
  },
  
  // Pulse content
  getPulse: async (runId: string) => {
    const response = await api.get(`/pulse/${runId}`);
    return response.data;
  },
  
  // Configuration
  getConfig: async () => {
    const response = await api.get('/config');
    return response.data;
  },
  
  updateConfig: async (config: any) => {
    const response = await api.put('/config', config);
    return response.data;
  },
  
  // Alerts
  getAlerts: async () => {
    const response = await api.get('/alerts');
    return response.data;
  },
  
  acknowledgeAlert: async (id: string) => {
    const response = await api.post(`/alerts/${id}/acknowledge`);
    return response.data;
  },
  
  // Analytics
  getAnalytics: async (params: any) => {
    const response = await api.get('/analytics', { params });
    return response.data;
  },
};
```

---

## Step 8: Build and Test Locally

Before deploying to Vercel:

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Test production build locally
npm start
```

Verify:
- All pages load correctly
- API calls work (or use mock data)
- Responsive design works on different screen sizes
- Environment variables are properly configured

---

## Step 9: Deploy to Vercel

### Option A: Via Vercel Dashboard (Recommended for first deployment)

1. **Push changes to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for Vercel deployment"
   git push
   ```

2. **Deploy from Vercel Dashboard:**
   - Go to your Vercel project
   - Click "Deploy"
   - Vercel will automatically build and deploy
   - Wait for deployment to complete (usually 2-5 minutes)

3. **Access your deployed site:**
   - Vercel will provide a URL like `https://your-project.vercel.app`
   - Test the deployed application

### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel

# For production deployment
vercel --prod
```

---

## Step 10: Configure Custom Domain (Optional)

1. **Add custom domain in Vercel:**
   - Go to Settings → Domains
   - Click "Add Domain"
   - Enter your domain (e.g., `dashboard.groww.com`)

2. **Configure DNS:**
   - Vercel will provide DNS records to add
   - Add A record or CNAME record to your DNS provider

3. **Wait for propagation:**
   - DNS changes can take 24-48 hours to propagate
   - Vercel will automatically provision SSL certificate

---

## Step 11: Set Up Monitoring and Analytics

### Vercel Analytics

```bash
npm install @vercel/analytics
```

Add to `app/layout.tsx`:

```typescript
import { Analytics } from '@vercel/analytics/react';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

### Error Tracking (Optional)

```bash
npm install @sentry/nextjs
npx @sentry/wizard@latest -i nextjs
```

---

## Step 12: Set Up CI/CD Pipeline

Vercel automatically deploys on push to main branch. For additional control:

### GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Run tests
        run: npm test
        
      - name: Build
        run: npm run build
        
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
```

---

## Step 13: Environment-Specific Configurations

### Development Environment

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_API_KEY=dev_key
```

### Staging Environment

```env
NEXT_PUBLIC_API_URL=https://staging-api.groww.com/api
NEXT_PUBLIC_API_KEY=staging_key
```

### Production Environment

```env
NEXT_PUBLIC_API_URL=https://api.groww.com/api
NEXT_PUBLIC_API_KEY=prod_key
```

---

## Step 14: Performance Optimization

### Enable Image Optimization

```javascript
// next.config.js
images: {
  formats: ['image/avif', 'image/webp'],
  deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
},
```

### Enable Static Generation Where Possible

```typescript
// app/page.tsx
export const revalidate = 3600; // Revalidate every hour
```

### Bundle Size Optimization

```bash
npm install @next/bundle-analyzer
```

Add to `next.config.js`:

```javascript
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer(nextConfig);
```

---

## Step 15: Security Best Practices

### 1. Environment Variables

- Never commit `.env.local` to Git
- Use `.env.example` for documentation
- Rotate API keys regularly

### 2. CORS Configuration

Configure CORS on your backend to allow requests from your Vercel domain:

```javascript
// Backend CORS configuration
const corsOptions = {
  origin: [
    'http://localhost:3000',
    'https://your-project.vercel.app',
    'https://dashboard.groww.com',
  ],
  credentials: true,
};
```

### 3. Rate Limiting

Implement rate limiting on your backend API to prevent abuse.

### 4. Security Headers

Add security headers in `next.config.js`:

```javascript
async headers() {
  return [
    {
      source: '/:path*',
      headers: [
        {
          key: 'X-DNS-Prefetch-Control',
          value: 'on'
        },
        {
          key: 'Strict-Transport-Security',
          value: 'max-age=63072000; includeSubDomains; preload'
        },
        {
          key: 'X-Frame-Options',
          value: 'SAMEORIGIN'
        },
        {
          key: 'X-Content-Type-Options',
          value: 'nosniff'
        },
        {
          key: 'X-XSS-Protection',
          value: '1; mode=block'
        },
      ],
    },
  ];
}
```

---

## Step 16: Post-Deployment Checklist

After deployment, verify:

- [ ] All pages load correctly
- [ ] API calls work in production
- [ ] Authentication works (if implemented)
- [ ] Responsive design works on mobile
- [ ] Environment variables are correctly set
- [ ] Custom domain (if configured) works
- [ ] SSL certificate is valid
- [ ] Analytics are tracking
- [ ] Error tracking is working (if configured)
- [ ] Performance metrics are acceptable
- [ ] Accessibility features work

---

## Troubleshooting

### Build Failures

**Issue:** Build fails on Vercel but works locally

**Solutions:**
- Check Node.js version compatibility
- Verify all dependencies are in `package.json`
- Check for platform-specific dependencies
- Review build logs in Vercel dashboard

### Environment Variables Not Working

**Issue:** Environment variables are undefined in production

**Solutions:**
- Ensure variables are prefixed with `NEXT_PUBLIC_` for client-side access
- Verify variables are added in Vercel dashboard
- Redeploy after adding environment variables

### API Calls Failing

**Issue:** API calls fail in production but work locally

**Solutions:**
- Check CORS configuration on backend
- Verify API URL is correct in production
- Check if API key is valid
- Review browser console for CORS errors

### Performance Issues

**Issue:** Slow page load times

**Solutions:**
- Enable image optimization
- Implement code splitting
- Use static generation where possible
- Optimize bundle size
- Enable caching

---

## Maintenance

### Regular Tasks

- **Weekly:** Check Vercel analytics and error logs
- **Monthly:** Update dependencies (`npm update`)
- **Quarterly:** Review and optimize performance
- **As needed:** Deploy bug fixes and new features

### Monitoring

- Monitor Vercel dashboard for errors
- Set up alerts for deployment failures
- Track performance metrics
- Review user feedback

---

## Cost Considerations

**Vercel Free Tier:**
- 100GB bandwidth per month
- Unlimited deployments
- 1000 serverless function invocations per month
- 6GB serverless function execution time per month

**Pro Plan ($20/month):**
- 1TB bandwidth per month
- Unlimited serverless function invocations
- 100GB serverless function execution time per month
- Priority support

**Enterprise Plan:** Contact Vercel for pricing

---

## Support and Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Next.js Documentation](https://nextjs.org/docs)
- [Vercel Community](https://vercel.com/community)
- [Next.js GitHub](https://github.com/vercel/next.js)

---

## Summary

This deployment plan covers:
1. ✅ Project initialization and setup
2. ✅ Dependency installation
3. ✅ Environment configuration
4. ✅ Vercel project setup
5. ✅ API client configuration
6. ✅ Local testing
7. ✅ Deployment to Vercel
8. ✅ Custom domain configuration
9. ✅ Monitoring and analytics
10. ✅ CI/CD pipeline setup
11. ✅ Performance optimization
12. ✅ Security best practices
13. ✅ Post-deployment verification
14. ✅ Troubleshooting guide
15. ✅ Maintenance guidelines

Follow these steps to successfully deploy your GROWW Weekly Review Pulse Agent Dashboard to Vercel.
