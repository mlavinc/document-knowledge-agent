# Martin Lavin Carvajal Portfolio

Personal portfolio for **Martin Lavin Carvajal**, Computer Engineering student focused on cloud engineering, AWS architecture, backend systems, and AI-powered applications.

The site presents selected projects as professional case studies, with optional live demos, architecture diagrams, and repository links.

## Stack

| Layer | Technology |
| --- | --- |
| Framework | [Next.js](https://nextjs.org/) 16 (App Router) |
| Language | TypeScript |
| UI | React 19, Tailwind CSS 4 |
| Motion | Framer Motion |
| Fonts | Geist |

## Features

- Dark, minimalist Vercel-inspired layout
- Hero, Projects, About, Skills, Contact, and Footer sections
- Project cards with thumbnails, tech tags, GitHub, Case Study, and Live Demo (when available)
- Dynamic case study pages at `/projects/[slug]`
- Embedded live demos for selected projects (iframe with fallback)
- Architecture diagrams and structured case study sections
- Subtle site-wide starfield background with reduced-motion support
- CV downloads (English / Spanish) from the Hero section

## Featured projects

| Project | Focus |
| --- | --- |
| [Document Knowledge Agent](https://github.com/mlavinc/document-knowledge-agent) | Cloud-native RAG on AWS |
| [Cloud Operations Lab](https://github.com/mlavinc/cloud-operations-lab) | Terraform, CI/CD, OIDC, SSM, observability |
| [ECG-AI Serverless](https://github.com/mlavinc/ecg-ai-serverless) | ML inference on AWS Lambda |
| [Skill Tracker](https://github.com/mlavinc/skill-tracker) | Full-stack Go + React + PostgreSQL |

## Project structure

```text
app/                  # Next.js App Router pages and layouts
components/
  layout/             # Navbar, Footer, cosmic background
  sections/           # Hero, Projects, About, Skills, Contact
  projects/           # Case study UI building blocks
  ui/                 # ProjectCard, LiveDemoEmbed
  motion/             # Page and reveal animations
data/                 # Projects, case studies, about, skills, contact
  case-studies/       # Per-project case study content
lib/                  # Helpers (projects, motion)
public/               # Static assets (project images, CVs)
types/                # Shared TypeScript types
```

Content is separated from UI: update `data/projects.ts` and `data/case-studies/*` to change portfolio copy without touching components.

## Getting started

### Requirements

- Node.js 20+ (recommended)
- npm

### Install

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Build

```bash
npm run build
npm start
```

### Lint

```bash
npm run lint
```

## Scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Start the development server |
| `npm run build` | Create a production build |
| `npm start` | Serve the production build |
| `npm run lint` | Run ESLint |

## Adding or updating a project

1. Add or update the entry in `data/projects.ts`.
2. Add or update the case study in `data/case-studies/<slug>.ts`.
3. Place images under `public/projects/` (thumbnail, architecture diagrams, etc.).
4. Set optional fields as needed:
   - `liveUrl` for Live Demo + embedded demo
   - `architectureImage` for the Architecture section
   - `githubUrl` for the repository button

## Author

**Martin Lavin Carvajal**

- Email: [martinlavinc@gmail.com](mailto:martinlavinc@gmail.com)
- LinkedIn: [martin-lavin-carvajal](https://www.linkedin.com/in/martin-lavin-carvajal-010b08339/)
- GitHub: [mlavinc](https://github.com/mlavinc)

## License

Private portfolio project. All rights reserved unless otherwise stated.
