# StorySpark

**AI-Powered Character Studio for Parents** — Create personalized clips featuring your child's favorite TV show characters to inspire storytelling, motivate chores, and spark learning.

> *"Hey Thomas! It's Frog! Toad and I were just talking about how brave you were cleaning up your room today. That reminds me of a story..."*

## The Problem

Every parent knows the struggle: getting kids to do chores, tell stories, or engage with learning. But every parent also knows what captures their child's attention — their favorite TV show characters. What if those characters could speak directly to your child, by name, encouraging them in ways that feel magical?

## The Solution

**StorySpark** is a studio where parents craft short, personalized audio/video clips featuring AI-generated versions of characters from their children's favorite shows. Parents select a character, choose a scenario (chore motivation, storytelling prompt, educational lesson), customize the message, and generate a clip their child will love.

### Built for Thomas (and every kid like him)

Our first supported show is **Frog & Toad** (Apple TV+). Thomas is obsessed. Now Frog and Toad can talk directly to him.

## Features

### v1 — Hackathon MVP
- **Character Library** — Frog, Toad, and friends with personality profiles and voice characteristics
- **Clip Creator** — Parents build clips by selecting characters, scenarios, and personalizing messages
- **AI Script Generation** — Claude generates scripts that are faithful to each character's voice and personality
- **Text-to-Speech** — Character-faithful voice generation
- **Clip Player** — Beautiful playback experience designed for kids
- **Scenario Templates** — Pre-built templates for common use cases:
  - Chore motivation ("Frog asks Thomas to help clean up")
  - Storytelling prompts ("Toad starts a story and asks Thomas what happens next")
  - Educational moments ("Frog teaches Thomas about seasons")
  - Bedtime wind-down ("Toad says goodnight to Thomas")
  - Positive reinforcement ("Frog celebrates Thomas's achievement")

### Future Vision
- Multiple show support (Bluey, Daniel Tiger, Sesame Street, etc.)
- Video clip generation with animated scenes
- Interactive mode — characters respond to child's voice
- Curriculum integration — align with school learning objectives
- Sharing between parents ("This Bluey chore clip worked great!")
- Mobile app with offline playback

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vite + React + TypeScript + Tailwind CSS + shadcn/ui |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| AI - Scripts | Claude API (Anthropic) |
| AI - Voice | TTS API (ElevenLabs / OpenAI) |
| AI - Orchestration | Claude Agent SDK |
| Infrastructure | Docker Compose (local dev) |

## Architecture

```
┌─────────────────────────────────────┐
│           StorySpark Frontend        │
│     (React + Vite + Tailwind)        │
│                                      │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ Character │  │  Clip Creator    │  │
│  │ Library   │  │  (Multi-step     │  │
│  │           │  │   wizard)        │  │
│  └──────────┘  └──────────────────┘  │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ Clip      │  │  Template        │  │
│  │ Player    │  │  Gallery         │  │
│  └──────────┘  └──────────────────┘  │
└──────────────┬──────────────────────┘
               │ REST API
┌──────────────▼──────────────────────┐
│          FastAPI Backend             │
│                                      │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ Clip API  │  │  Character API   │  │
│  └──────────┘  └──────────────────┘  │
│  ┌──────────┐  ┌──────────────────┐  │
│  │ Template  │  │  AI Agent        │  │
│  │ API       │  │  Orchestrator    │  │
│  └──────────┘  └──────────────────┘  │
└──────┬───────────────┬──────────────┘
       │               │
┌──────▼──────┐ ┌──────▼──────────────┐
│  PostgreSQL  │ │   AI Services       │
│              │ │  ┌────────────────┐  │
│  - Users     │ │  │ Claude API     │  │
│  - Children  │ │  │ (Scripts)      │  │
│  - Shows     │ │  │                │  │
│  - Characters│ │  │ TTS API        │  │
│  - Clips     │ │  │ (Voice Gen)    │  │
│  - Templates │ │  └────────────────┘  │
└─────────────┘ └─────────────────────┘
```

## Quick Start

```bash
# Clone and start
git clone git@github.com:dominicphillips/claude-opus-hackathon.git
cd claude-opus-hackathon
cp .env.example .env  # Add your API keys
docker-compose up -d

# Frontend runs on http://localhost:5173
# Backend runs on http://localhost:8000
# API docs at http://localhost:8000/docs
```

## Project Structure

```
storyspark/
├── frontend/                 # Vite + React + TypeScript
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── ui/           # shadcn/ui components
│   │   │   ├── clip-creator/ # Clip creation wizard
│   │   │   ├── player/       # Clip playback
│   │   │   └── characters/   # Character browser
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utilities
│   │   ├── pages/            # Route pages
│   │   └── types/            # TypeScript types
│   └── ...
├── backend/                  # Python + FastAPI
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── agents/           # AI agent definitions
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── core/             # Config, deps, etc.
│   └── ...
├── docker-compose.yml
├── AGENTS.md
└── README.md
```

## Team

Built with love (and AI) for the **Claude Opus Hackathon 2025**.

---

*StorySpark is a hackathon project. Character likenesses are used for demonstration purposes only. We are not affiliated with Apple TV+ or any show creators.*
