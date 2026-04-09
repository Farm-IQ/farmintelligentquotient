# FarmIQ Frontend - AI-Powered Agricultural Intelligence Platform

> **Multi-role, cloud-native Angular 21 PWA** for smallholder farmers in Kenya  
> **Status**: Production-ready (v1.0) | **Last Updated**: 2026-04-02

---

## 📋 Executive Summary

FarmIQ Frontend is a **Progressive Web Application (PWA)** built with **Angular 21** that provides role-based dashboards and intelligent features for agricultural stakeholders:

- 🌾 **Farmers**: Farm management, credit scoring, market insights, AI chatbot
- 👷 **Workers**: Task tracking, attendance, payroll, performance analytics
- 👔 **Admin**: Platform management, user administration, tokenomics, payments
- 🏦 **Lenders**: Loan portfolios, risk assessment, disbursement tracking
- 🤝 **Cooperatives**: Group coordination, member management
- 🚚 **Vendors/Agents**: Sales management, field operations

### Key Highlights
- ✅ **8 Role-Based Modules** with unique dashboards and features
- ✅ **FarmGrow RAG Chatbot** - Agricultural Q&A with document uploads
- ✅ **AI-Powered Credit Scoring** - Farmer loan eligibility assessment
- ✅ **Real-time Analytics** - Production, market, and financial metrics
- ✅ **Mobile-First PWA** - Works offline, installable on home screen
- ✅ **Server-Side Rendering (SSR)** - Fast initial load, SEO-optimized
- ✅ **Blockchain Integration** - Hedera for immutable transactions
- ✅ **Multi-Channel Support** - Web (desktop/mobile), USSD, SMS

---

## 🚀 Quick Start

### Prerequisites
```bash
Node.js 18+ (tested on 20.x)
npm 11.6.2+
Angular CLI 21.1.1+
```

### Installation & Development

```bash
# 1. Install dependencies
npm install

# 2. Set up environment variables
cp .env.example .env.development.local
# Edit with your Supabase & FastAPI credentials

# 3. Start development server
npm start
# OR
ng serve

# Open browser: http://localhost:4200
```

### Environment Configuration

Create `.env.development.local` or `.env.production`:

```typescript
# Supabase (Authentication & Database)
VITE_SUPABASE_URL=https://your-supabase-instance.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ0eXAiOiJKV1QiLCJhbGc...

# FastAPI Backend
VITE_API_URL=http://localhost:8000/api/
VITE_BACKEND_URL=http://localhost:8000/api/

# OAuth Callbacks
VITE_AUTH_CALLBACK_URL=/auth-callback
VITE_AUTH_CALLBACK_FULL_URL=http://localhost:4200/auth-callback

# Africa's Talking (SMS/USSD)
VITE_AFRICAS_TALKING_API_KEY=your_key
VITE_AFRICAS_TALKING_USERNAME=FarmIQ

# Hedera Blockchain (Optional)
VITE_HEDERA_ACCOUNT_ID=0.0.xxxxx
VITE_HEDERA_PRIVATE_KEY=302e020...
VITE_HEDERA_NETWORK=testnet

# GIS/Mapping
VITE_TOMTOM_API_KEY=your_tomtom_key
VITE_TOMTOM_STYLE_URL=https://api.tomtom.com/style/...
```

---

## 📁 Project Structure

```
farmiq/
├── src/
│   ├── app/
│   │   ├── app.ts                          # Root component
│   │   ├── app.routes.ts                   # Global routing config
│   │   ├── app.config.ts                   # Angular providers & interceptors
│   │   ├── app.html                        # Root template
│   │   ├── app.scss                        # Root styles
│   │   │
│   │   ├── components/                     # Shared components
│   │   │   ├── landing/                    # Landing page
│   │   │   ├── farmgrow-chatbot/           # RAG chatbot interface
│   │   │   └── pwa-install-banner/         # PWA install prompt
│   │   │
│   │   ├── modules/                        # 8 role-based feature modules
│   │   │   ├── auth/                       # Authentication (login, signup, guards)
│   │   │   ├── farmer/                     # 🌾 Farmer dashboard (10+ components)
│   │   │   ├── worker/                     # 👷 Worker dashboard (10+ components)
│   │   │   ├── admin/                      # 👔 Admin dashboard (12+ components)
│   │   │   ├── lender/                     # 🏦 Lender portfolio views
│   │   │   ├── cooperative/                # 🤝 Group coordination
│   │   │   ├── agent/                      # 🤖 Field agent tools
│   │   │   └── vendor/                     # 🚚 Vendor sales management
│   │   │
│   │   ├── services/
│   │   │   ├── core/                       # Core infrastructure
│   │   │   │   ├── supabase.service.ts     # Auth + DB (Signals-based)
│   │   │   │   ├── farmiq-id.service.ts    # FarmIQ ID generation
│   │   │   │   ├── hedera-sdk.service.ts   # Blockchain integration
│   │   │   │   └── error-handling.service.ts
│   │   │   ├── rag/                        # RAG chatbot services
│   │   │   │   ├── farmgrow-chatbot.service.ts
│   │   │   │   ├── rag-management.service.ts
│   │   │   │   ├── embedding-storage.service.ts
│   │   │   │   └── permission.service.ts
│   │   │   └── pwa/                        # Progressive Web App
│   │   │       └── pwa.ts
│   │   │
│   │   ├── interceptors/                   # HTTP interceptors
│   │   │   ├── core/
│   │   │   │   ├── api-interceptor.ts      # Add FarmIQ ID header
│   │   │   │   └── error-interceptor.ts    # Global error handling
│   │   │   └── index.ts
│   │   │
│   │   ├── models/                         # TypeScript interfaces
│   │   │   ├── rag-chatbot.models.ts
│   │   │   └── index.ts
│   │   │
│   │   └── app.scss                        # Global styles
│   │
│   ├── environments/
│   │   ├── environment.ts                  # Production config
│   │   └── environment.development.ts      # Development config
│   │
│   ├── index.html                          # PWA manifest, meta tags
│   ├── main.ts                             # Browser bootstrap
│   ├── main.server.ts                      # SSR bootstrap
│   ├── server.ts                           # Express SSR server
│   ├── styles.scss                         # Global styles & design system
│   └── favicon.ico
│
├── public/                                 # Static assets
│   ├── icons/                              # PWA icons (various sizes)
│   ├── manifest.webmanifest                # PWA manifest
│   └── browserconfig.xml                   # Windows tile config
│
├── .angular/                               # Angular CLI cache
├── angular.json                            # Angular build config
├── tsconfig.json                           # TypeScript config
├── tsconfig.app.json
├── tsconfig.spec.json
├── package.json
├── package-lock.json
├── .editorconfig
├── .gitignore
├── .env.development     (template)
├── .env.example         (template)
├── .env.local           (current)
├── .env.production      (template)
├── README.md            (this file)
└── ngsw-config.json     # Service Worker configuration
```

---

## 🏗️ Architecture Overview

### Layered Architecture

```
┌─────────────────────────────────────────┐
│  PRESENTATION LAYER (Components)        │
│  ├─ Route handlers & pages              │
│  ├─ Form inputs & validation            │
│  ├─ Data display (tables, charts)       │
│  └─ User interactions                   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  SERVICE LAYER (Business Logic)         │
│  ├─ API integration (Supabase, FastAPI) │
│  ├─ Data transformation                 │
│  ├─ State management (Signals/RxJS)     │
│  └─ Authentication & Authorization      │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  INFRASTRUCTURE LAYER                   │
│  ├─ HTTP Client (interceptors)          │
│  ├─ Guards & Route protection           │
│  ├─ Error handling & logging            │
│  └─ Configuration management            │
└──────────────┬──────────────────────────┘
               ↓
      ┌────────┴────────┐
      ↓                 ↓
   Supabase         FastAPI Backend
   (Auth, DB)       (Business Logic)
```

### Authentication Flow

```
LOGIN/SIGNUP
    ↓
Supabase Auth
    ↓
Session + FarmIQ ID (generated if new user)
    ↓
FarmIQ ID stored in signal (app state)
    ↓
X-FarmIQ-ID header injected in all API requests
    ↓
Role-based module loaded via lazy loading
    ↓
Guards verify access before rendering dashboard
```

### State Management (Angular 21 Signals)

```typescript
// Reactive state in SupabaseService
farmiqIdSignal = signal<string | null>(null);
userSignal = signal<AuthUser | null>(null);
isAuthenticatedSignal = signal<boolean>(false);
sessionSignal = signal<Session | null>(null);

// Components subscribe via async pipe
{{ farmiqIdSignal$ | async }}

// Or in component class
farmiqId = toSignal(this.supabaseService.farmiqIdSignal$);
```

---

## 🔐 Authentication & Authorization

### Authentication Methods

1. **Email/Password** ✅
   - Sign up with email verification
   - Login with credentials
   - Password reset via email

2. **OAuth (Google, GitHub, etc.)** ✅
   - One-click sign up
   - No password required
   - Role selection modal on first login

3. **FarmIQ ID Header** ✅
   - Custom header: `X-FarmIQ-ID: FQ7K9M2X`
   - Added to all API requests automatically
   - Backend uses this for user context

### Guards & Access Control

```typescript
// Route protection
{
  path: 'farmer',
  canActivate: [farmerGuard],        // Role check
  loadChildren: () => import('./farmer-module')
}

// Guard implementations
authGuard          → Is user authenticated?
farmiqIdGuard      → Valid FarmIQ ID?
farmerGuard        → User role is 'farmer'?
workerAuthGuard    → User role is 'worker'?
adminGuard         → User role is 'admin'?
roleGuard          → Generic role-based access
```

### FarmIQ ID Generation

```typescript
// Format: FQ + 4 random alphanumeric characters
// Examples: FQ7K9M2, FQX7L4P, FQPD8WR

// Service auto-generates on signup
farmiqIdService.generateUniqueFarmiqIdWithResult()
  .then(result => {
    if (result.success) {
      console.log('Generated ID:', result.farmiqId);  // FQ7K9M2X
    }
  });

// Validation
FarmiqIdValidator.isValidFormat('FQ7K9M2X')  // true
```

---

## 🌐 8 Role-Based Modules

### 1. 🌾 Farmer Module
**Path**: `/farmer`  
**Target User**: Smallholder farmers  

**Key Features**:
- 📊 Dashboard with farm KPIs
- 📈 Analytics (production, revenue, expenses)
- 💳 Credit score & loan eligibility
- 💰 Wallet (FIQ token balance, transaction history)
- 🚜 Farm setup wizard (county, crops, livestock)
- 📋 Account management & settings
- 📢 Market insights & price trends

**Components**: 10+
- `farmer-dashboard` - Main farm overview
- `farmer-analytics` - Charts & metrics
- `farmer-credit-score` - Score explainability
- `farmer-wallet` - Token management
- `farmer-account` - Profile
- `farmer-market-insights` - Market data
- `farm-setup-wizard` - 4-step onboarding

### 2. 👷 Worker Module
**Path**: `/worker`  
**Target User**: Farm laborers, field workers  

**Key Features**:
- ✅ Attendance tracking (clock in/out)
- 📋 Task assignment & completion
- 📊 Performance metrics
- 💵 Payroll management
- 🛠️ Equipment tracking
- 📈 Productivity analytics
- 📱 Mobile-optimized interface

**Components**: 10+
- `worker-dashboard` - Home screen
- `worker-attendance-tracker` - Time tracking
- `worker-task-manager` - Task list
- `worker-performance-tracker` - KPIs
- `worker-payroll-manager` - Salary info

### 3. 👔 Admin Module
**Path**: `/admin`  
**Target User**: Platform administrators  

**Key Features**:
- 👥 User management & roles
- 💳 Payment reconciliation
- 🪙 Tokenomics & supply tracking
- 🤖 ML model deployment & monitoring
- 📋 Data governance & compliance
- ⛓️ Hedera HCS management
- 📊 System health dashboard

**Components**: 12+
- `admin-dashboard` - System overview
- `admin-user-management` - User CRUD
- `admin-payment-management` - Payment tracking
- `admin-tokenomics` - Token analytics
- `admin-model-operations` - ML model mgmt
- `admin-data-governance` - Compliance

### 4. 🏦 Lender Module
**Path**: `/lender`  
**Target User**: Microfinance institutions, banks  

**Key Features**:
- 📊 Loan portfolio dashboard
- 🔍 Farmer credit score review
- ✅ Loan application approval workflow
- 💸 Disbursement tracking
- 📈 Risk assessment
- 📋 Repayment schedules
- 🎯 Performance reports

### 5. 🤝 Cooperative Module
**Path**: `/cooperative`  
**Target User**: Farmer groups, cooperatives  

**Key Features**:
- 👥 Member management
- 📊 Group analytics
- 📢 Announcements & messages
- 💰 Group fund tracking
- 📋 Meeting schedules
- 📈 Collective market insights

### 6. 🤖 Agent Module
**Path**: `/agent`  
**Target User**: Field agents, supervisors  

**Key Features**:
- 🆔 Agent verification workflow
- 💼 Performance tracking
- 💰 Agent wallet (commissions)
- 📝 Farmer onboarding reports
- 📊 Territory analytics

### 7. 🚚 Vendor Module
**Path**: `/vendor`  
**Target User**: Input suppliers, service providers  

**Key Features**:
- 🛒 Product catalog management
- 📊 Sales dashboard
- 💳 Payment tracking
- 📦 Inventory management
- 👥 Customer management

### 8. 📱 Cooperative (Worker) Module
**Path**: `/cooperative`  
**Target User**: Group-based operations  

**Key Features**:
- Similar to Farmer but for collective data
- Shared resources & tools
- Group decision support

---

## 💬 FarmGrow RAG Chatbot

### Features
- 🤖 AI-powered agricultural Q&A
- 📄 Document upload & processing (PDF, images)
- 🎤 Voice input support (future)
- 📸 Image recognition for crop problems
- 💡 Relevant document retrieval
- 📊 Query confidence scores
- 💾 Conversation history

### Usage

```typescript
// Service integration
import { FarmGrowChatbotService } from './services/rag/farmgrow-chatbot.service';

constructor(private chatbot: FarmGrowChatbotService) {}

// Send query
this.chatbot.sendMessage({
  message: 'How do I treat maize blight?',
  crop_type: 'Maize',
  farm_location: 'Central Kenya',
  stream: true  // Enable streaming
}).pipe(
  tap(response => console.log(response.response))
).subscribe();

// Upload document
this.chatbot.uploadDocument(file).subscribe(result => {
  console.log('Document indexed:', result.document_id);
});
```

### API Integration
- Backend: FastAPI `/api/v1/farmgrow/chat`
- Streaming support for real-time responses
- Token usage tracking (FIQ tokens)
- Conversation persistence

---

## 🛠️ Development Commands

### Session & Dev Tools

```bash
# Start development server (hot reload)
npm start
ng serve

# Open browser
# http://localhost:4200

# Development with specific configuration
ng serve --configuration development --host 0.0.0.0 --port 3000

# Build for production
npm run build
ng build --configuration production

# Build for development
ng build --configuration development

# Watch mode (rebuild on changes, no serve)
npm run watch

# Run unit tests
npm test
ng test

# Run tests in watch mode
ng test --watch

# Generate test coverage report
ng test --code-coverage

# Format code with Prettier
npx prettier --write "src/**/*.{ts,html,scss}"

# Lint check
ng lint  (if ESLint configured)
```

### SSR (Server-Side Rendering)

```bash
# Build SSR version
ng build --configuration production

# Start SSR server
npm run serve:ssr:farmiq

# Server runs on: http://localhost:4000
```

---

## 📦 Building & Deployment

### Production Build

```bash
# 1. Build the application
npm run build

# Output: dist/farmiq/
# ├── browser/          (Client-side code)
# ├── server/           (SSR server code)
# └── prerender-manifest.json

# 2. Verify production build locally
npm run serve:ssr:farmiq

# 3. Deploy to hosting (see Deployment section)
```

### Build Optimizations

- ✅ Tree shaking (unused code removal)
- ✅ Code splitting (lazy loading modules)
- ✅ Minification & compression (gzip/brotli)
- ✅ Image optimization (WebP, responsive)
- ✅ Bundling & cache busting (hash filenames)

### Bundle Size Analysis

```bash
# View bundle size breakdown
npm install -g source-map-explorer

source-map-explorer 'dist/farmiq/browser/**/*.js'

# Budget targets (angular.json)
# Initial: 1MB warning, 2MB error
# Component styles: 30KB warning, 50KB error
```

---

## 🧪 Testing

### Test Framework: Vitest

```bash
# Run all tests
npm test
ng test

# Run tests in watch mode
ng test --watch

# Run specific test file
ng test --include='**/farmer.service.spec.ts'

# Generate coverage report
ng test --code-coverage

# Coverage output: coverage/
```

### Test File Structure

```typescript
// farmer.service.spec.ts
import { TestBed } from '@angular/core/testing';
import { FarmerService } from './farmer.service';

describe('FarmerService', () => {
  let service: FarmerService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(FarmerService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch farmer profile', () => {
    service.getProfile('FQ7K9M2X').subscribe(profile => {
      expect(profile.name).toBeDefined();
    });
  });
});
```

### Test Coverage Target

- 🎯 Overall: 70%+
- Unit tests: Services, pipes, utilities (90%+)
- Component tests: Key routes & interactions (60%+)
- E2E tests: Critical user workflows (coverage TBD)

---

## 📚 Code Generation

### Generate New Component

```bash
# Create component in farmer module
ng generate component modules/farmer/components/new-component

# Generated files:
# ├── modules/farmer/components/new-component/
# │   ├── new-component.ts          (Component class)
# │   ├── new-component.html        (Template)
# │   ├── new-component.scss        (Styles)
# │   └── new-component.spec.ts     (Test)
```

### Generate New Service

```bash
# Create service in farmer module
ng generate service modules/farmer/services/new-service

# Generated files:
# ├── modules/farmer/services/
# │   ├── new-service.ts            (Service class)
# │   └── new-service.spec.ts       (Test)
```

### Code Generation Help

```bash
ng generate --help                      # All schematics
ng generate component --help            # Component options
ng generate service --help              # Service options
```

---

## 🎨 Styling & Design System

### Global Theme

Located in `src/styles.scss`:

```scss
// Primary brand color (Emerald)
--color-primary: #10B981
--color-primary-dark: #059669

// Secondary (Amber)
--color-accent: #F59E0B

// Status colors
--color-success: #10B981     (Green)
--color-danger: #EF4444      (Red)
--color-warning: #F59E0B     (Orange)
--color-info: #3B82F6        (Blue)

// Font system
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto
font-size-base: 16px

// Responsive breakpoints
sm: 640px   md: 768px   lg: 1024px   xl: 1280px
```

### Component Styling

```typescript
@Component({
  selector: 'app-my-component',
  templateUrl: './my-component.html',
  styleUrls: ['./my-component.scss']  // SCSS per component
})
export class MyComponent { }
```

### BEM Naming Convention

```scss
.block { }
.block__element { }
.block--modifier { }

// Example:
.farmer-dashboard { }
.farmer-dashboard__card { }
.farmer-dashboard--loading { }
```

---

## 📱 PWA & Mobile Features

### Progressive Web App Capabilities

✅ **Installable**
- Install icon in browser address bar
- Add to home screen (iOS & Android)
- Standalone app experience

✅ **Offline Support**
- Service worker caches static assets
- Works without internet connection
- Syncs when back online

✅ **Push Notifications** (future)
- Real-time alerts
- Subscription management

✅ **Mobile Optimized**
- Touch-friendly interface
- Responsive design
- Mobile-first CSS

### PWA Files

```
public/
├── manifest.webmanifest       # PWA metadata
├── browserconfig.xml          # Windows tile config
├── icons/
│   ├── icon-192x192.png       # Android home screen
│   ├── icon-512x512.png       # Android splash screen
│   └── apple-touch-icon.png   # iOS home screen
```

### Service Worker

Located in `ngsw-config.json`:

```json
{
  "index": "/index.html",
  "assetGroups": [
    {
      "name": "app",
      "installMode": "prefetch",
      "resources": {
        "files": ["/favicon.ico", "/**/*.js", "/**/*.css"]
      }
    },
    {
      "name": "assets",
      "installMode": "lazy",
      "resources": {
        "files": ["/assets/**"]
      }
    }
  ]
}
```

---

## 🌐 Environment Configuration

### Development Environment

**`.env.development.local`**:
```
VITE_SUPABASE_URL=http://localhost:3000
VITE_API_URL=http://localhost:8000/api/
VITE_ENVIRONMENT=development
VITE_DEBUG=true
```

### Production Environment

**`.env.production`**:
```
VITE_SUPABASE_URL=https://production.supabase.co
VITE_API_URL=https://api.farmiq.com/api/
VITE_ENVIRONMENT=production
VITE_DEBUG=false
```

### Loading Environment Variables

In components/services:

```typescript
import { environment } from '../environments/environment';

// Access config
console.log(environment.supabase.url);
console.log(environment.apiUrl);
```

---

## 🚀 Deployment

### Deploy to Vercel (Recommended)

```bash
# 1. Push code to GitHub
git push origin main

# 2. Connect GitHub repository to Vercel
# Vercel auto-deploys on push

# 3. Set environment variables in Vercel dashboard
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
VITE_API_URL=...

# 4. Vercel auto-builds and deploys
```

### Deploy to Firebase Hosting

```bash
# 1. Install Firebase CLI
npm install -g firebase-tools

# 2. Login
firebase login

# 3. Initialize Firebase
firebase init hosting

# 4. Build & deploy
npm run build
firebase deploy

# Live URL provided after deployment
```

### Deploy to Azure Static Web Apps

```bash
# 1. Create Azure resource
# App Service > Static Web App

# 2. Connect GitHub repository
# Auto-deploy on push

# 3. Set environment variables
# Configuration > Environment variables

# 4. GitHub Actions triggers build/deploy automatically
```

### Docker Deployment

**`Dockerfile`** (example):
```dockerfile
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY --from=build /app/dist ./dist
EXPOSE 4000
CMD ["npm", "run", "serve:ssr:farmiq"]
```

```bash
# Build image
docker build -t farmiq-frontend:latest .

# Run container
docker run -p 4000:4000 farmiq-frontend:latest
```

---

## 🔗 API Integration Points

### Backend Endpoints Used

| Module | Endpoint | Method | Purpose |
|--------|----------|--------|---------|
| **FarmGrow** | `/api/v1/farmgrow/chat` | POST | RAG chatbot queries |
| **FarmScore** | `/api/v1/farmscore/score` | POST | Credit score calculation |
| **FarmSuite** | `/api/v1/farmsuite/predict/yield` | POST | Yield prediction |
| **Payments** | `/api/v1/payments/initiate` | POST | M-Pesa STK push |
| | `/api/v1/mpesa/token-purchase` | POST | Token purchase via M-Pesa |
| **AI Usage** | `/api/v1/ai-usage/log` | POST | Token usage tracking |

### Request Headers

All requests include:
```
Authorization: Bearer {jwt_token}          # Supabase JWT
X-FarmIQ-ID: FQ7K9M2X                     # FarmIQ ID (critical)
X-User-Role: farmer                       # User role (optional)
Content-Type: application/json             # JSON format
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "X-FarmIQ-ID is missing" error
**Cause**: FarmIQ ID not loaded from Supabase  
**Solution**:
```bash
# Check Supabase connection in console
# Verify FarmIQ ID is in user_profiles table
# Restart dev server: Ctrl+C, npm start
```

#### 2. "Supabase client not initialized"
**Cause**: Environment variables missing  
**Solution**:
```bash
# Check .env.development.local exists
# Verify SUPABASE_URL and SUPABASE_ANON_KEY
# Reload browser: Ctrl+Shift+R (clear cache)
```

#### 3. "CORS error when calling backend"
**Cause**: Backend not running or wrong URL  
**Solution**:
```bash
# Verify FastAPI backend is running on localhost:8000
# Check BACKEND_URL in environment config
# Verify CORS is enabled in FastAPI main.py
```

#### 4. "Service worker not registering"
**Cause**: Running in development mode  
**Solution**:
```bash
# Service workers only work in production
# Build: npm run build
# Serve: npm run serve:ssr:farmiq
# Then test PWA features
```

### Debug Mode

Enable debug logging:

```typescript
// In environment.ts
export const environment = {
  production: false,
  debug: true,    // Enable debug mode
};

// In services
if (environment.debug) {
  console.log('Debug:', data);
}
```

---

## 📖 Additional Resources

### Official Documentation
- [Angular 21 Docs](https://angular.io/docs)
- [Angular CLI](https://angular.dev/tools/cli)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [RxJS](https://rxjs.dev/)
- [Angular Signals](https://angular.io/guide/signals)

### Key Libraries
- [Supabase JS Client](https://supabase.com/docs/reference/javascript)
- [Ionic Components](https://ionicframework.com/docs/components)
- [ngx-toastr](https://ngx-toastr.dev/)
- [Mapbox GL](https://docs.mapbox.com/mapbox-gl-js/)

### Related Projects
- Backend FastAPI: `farmiq-backend/`
- Database Migrations: `supabase/migrations/`
- Landing Page: Coming soon

---

## 📞 Support & Contribution

### Getting Help
- 📧 Email: support@farmiq.com
- 💬 Slack: #farmiq-frontend
- 📝 Issues: GitHub Issues
- 📚 Wiki: Internal documentation

### Contributing
1. Create feature branch: `git checkout -b feature/my-feature`
2. Commit changes: `git commit -m 'Add my feature'`
3. Push to branch: `git push origin feature/my-feature`
4. Open Pull Request

### Code Standards
- TypeScript strict mode enabled
- Angular style guide compliance
- 70%+ test coverage required
- Prettier formatting enforced
- No console.logs in production

---

## 📄 License

Copyright © 2026 FarmIQ. All rights reserved.

---

**Last Updated**: 2026-04-02 | **Version**: 21.1.1 | **Status**: ✅ Production Ready
