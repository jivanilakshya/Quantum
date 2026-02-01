# Quantum - AI-Powered Meeting Intelligence Platform

> Transform your meetings with AI-powered transcription, emotion analysis, and smart task management.

![Quantum Logo](https://img.shields.io/badge/Quantum-AI%20Meeting%20Intelligence-purple?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js-16.1-black?style=flat-square&logo=next.js)
![React](https://img.shields.io/badge/React-19.2-blue?style=flat-square&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?style=flat-square&logo=typescript)
![shadcn/ui](https://img.shields.io/badge/shadcn/ui-Latest-purple?style=flat-square)

## 🎯 Overview

**Quantum** is an enterprise-grade AI-powered meeting intelligence platform built for the MSBC Hackathon. It transforms meetings into actionable insights with:

- 🎙️ **Real-time transcription** with speaker differentiation
- 🧠 **AI summarization** extracting decisions and action items
- ✅ **Smart task management** with auto-ticket creation
- 😊 **Emotion analysis** tracking sentiment and engagement
- 📅 **Smart follow-ups** reducing meeting overload
- 🌍 **Multilingual support** (English, Hindi, Gujarati)
- 🔐 **Privacy-first** with local processing options

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- Git
- Vexa AI API Key (get from [vexa.ai/dashboard/api-keys](https://vexa.ai/dashboard/api-keys))

### Frontend Setup

```bash
# Navigate to frontend directory
cd quantum-frontend

# Install dependencies
npm install

# Create .env.local file with:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Backend Setup

```bash
# Navigate to backend directory
cd quantum-backend

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Vexa API key:
# VEXA_API_KEY=your_vexa_api_key_here
# VEXA_BASE_URL=https://api.cloud.vexa.ai
# SECRET_KEY=your-secret-key-here
# DATABASE_URL=sqlite:///./quantum.db
# FRONTEND_URL=http://localhost:3000

# Run the server
python main.py
```

The API will be available at [http://localhost:8000](http://localhost:8000)

**API Documentation**: http://localhost:8000/docs

## 🛠 Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **React 19** - Latest React with TypeScript
- **shadcn/ui** - Exclusive UI component library (Radix UI + Tailwind CSS)
- **Framer Motion** - Smooth animations
- **Recharts** - Data visualization
- **dnd-kit** - Drag-and-drop functionality
- **next-themes** - Dark/Light mode support
- **TipTap** - Rich text editor (ready for notes)
- **date-fns** - Date formatting

### Styling
- **Tailwind CSS** - Utility-first CSS
- **CSS Variables** - Dynamic theming
- **Responsive Design** - Mobile-first approach

## 📁 Project Structure

```
quantum-frontend/
├── app/                          # Next.js App Router
│   ├── page.tsx                 # Landing page
│   ├── layout.tsx               # Root layout with theme provider
│   ├── globals.css              # Global styles
│   ├── auth/
│   │   ├── login/page.tsx       # Login page
│   │   └── signup/page.tsx      # Signup page
│   ├── dashboard/page.tsx       # Dashboard with KPIs
│   ├── meetings/[id]/page.tsx   # Meeting intelligence
│   ├── tasks/page.tsx           # Kanban task board
│   ├── calendar/page.tsx        # Smart calendar
│   └── analytics/
│       └── emotion/page.tsx     # Emotion analytics
├── components/
│   ├── ui/                      # shadcn/ui components
│   ├── theme-provider.tsx       # Theme context provider
│   └── theme-toggle.tsx         # Dark/Light mode toggle
├── lib/
│   ├── utils.ts                 # Utility functions
│   └── mock-data.ts             # Demo data
└── public/                      # Static assets
```

## ✨ Features

### 1. Landing Page
- Modern hero section with gradient design
- Feature showcase with 6 core capabilities
- Privacy-first messaging
- Responsive layout

### 2. Authentication
- Login/Signup with form validation
- Role-based access control (RBAC)
- Toast notifications
- Secure password handling (ready for backend)

### 3. Dashboard
- **KPI Cards**: Total meetings, tasks created, follow-ups, emotion score
- **Charts**: Meeting trends (bar chart), emotion trends (line chart)
- **Recent Meetings**: Clickable list with summaries
- **Activity Feed**: Real-time updates

### 4. Meeting Intelligence
- **AI Summary**: Crisp meeting overview
- **Transcript**: Full transcript with speaker diarization
- **Decisions**: Extracted key decisions
- **Action Items**: Table with owner, due date, priority, status
- **Emotion Preview**: Overall score and timeline

### 5. Task Board
- **Kanban Layout**: To Do, In Progress, Done columns
- **Drag-and-Drop**: Interactive task movement
- **Task Cards**: Priority badges, due dates, owner avatars
- **Integrations**: Jira, Trello, Asana connection buttons

### 6. Smart Calendar
- **Calendar Component**: Interactive date selection
- **Upcoming Meetings**: List with time and participants
- **AI Follow-ups**: Smart suggestions based on context
- **Calendar Sync**: Google Calendar, Outlook integration options

### 7. Emotion Analytics
- **Overview Cards**: Overall score, positive moments, engagement, concerns
- **Emotion Timeline**: Line chart showing emotional flow
- **Distribution**: Pie chart of sentiment breakdown
- **Speaker Analysis**: Individual emotion profiles with badges

## 🎨 Design System

### shadcn/ui Components Used
- ✅ Button, Card, Input, Label, Select
- ✅ Dialog, Dropdown Menu, Tabs, Badge
- ✅ Table, Calendar, Avatar, Progress
- ✅ Sonner (Toasts), Sheet, Separator, Switch, Alert

### Color Palette
- **Primary**: Purple (#9333ea) to Blue (#2563eb) gradients
- **Success**: Green (#10b981)
- **Warning**: Orange (#f59e0b)
- **Error**: Red (#ef4444)
- **Neutral**: Gray scale with dark mode support

### Typography
- **Font**: Inter (Google Fonts)
- **Headings**: Bold, gradient text for emphasis
- **Body**: Regular weight, optimized for readability

## 🔐 Privacy & Security

- **Local Processing**: Option for on-device AI processing
- **End-to-End Encryption**: Ready for implementation
- **On-Premise Deployment**: Architecture supports self-hosting
- **GDPR Compliant**: Privacy-first data handling

## 📊 Mock Data

The application includes comprehensive mock data for demo purposes:
- 2 sample meetings with full transcripts
- 4 action items with realistic details
- Emotion analysis data with timelines
- Dashboard statistics and trends

## 🧪 Testing

### Manual Testing
All pages have been tested in the browser:
- ✅ Landing page loads with animations
- ✅ Authentication forms validate correctly
- ✅ Dashboard displays KPIs and charts
- ✅ Meeting intelligence shows all tabs
- ✅ Task board supports drag-and-drop
- ✅ Calendar displays meetings and AI suggestions
- ✅ Emotion analytics renders all visualizations

### Browser Compatibility
- Chrome/Edge (Chromium) ✅
- Firefox ✅
- Safari ✅

## 🚧 Future Enhancements

### Backend Integration
- [ ] FastAPI backend setup
- [ ] PostgreSQL database
- [ ] JWT authentication
- [ ] WebSocket for real-time updates

### AI Module Integration
- [ ] Vexa Meeting Bot (transcription)
- [ ] Langflow (LLM orchestration)
- [ ] Sales Emotion Analysis module

### Third-Party Integrations
- [ ] Jira API
- [ ] Trello API
- [ ] Asana API
- [ ] Google Calendar API
- [ ] Outlook Calendar API

### Advanced Features
- [ ] PDF report generation
- [ ] Admin panel for user management
- [ ] Multilingual UI
- [ ] Video recording upload
- [ ] Live meeting transcription

## 📝 Scripts

```bash
# Development
npm run dev          # Start dev server with Turbopack

# Production
npm run build        # Build for production
npm run start        # Start production server

# Code Quality
npm run lint         # Run ESLint
```

## 🤝 Contributing

This is a hackathon project. For production use, please:
1. Implement proper authentication
2. Connect to real backend services
3. Add comprehensive testing
4. Set up CI/CD pipeline

## 📄 License

Built for MSBC Hackathon 2026.

## 🏆 Acknowledgments

- **shadcn/ui** - Beautiful component library
- **Vercel** - Next.js framework
- **Radix UI** - Accessible primitives
- **Tailwind CSS** - Utility-first CSS

---

**Built with ❤️ for the MSBC Hackathon**

For questions or demo requests, please contact the development team.
