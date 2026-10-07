# n8n Ultimate Scraper & ResearchForge AI Agent

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF_Generation-red?style=flat)](https://www.reportlab.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

An intelligent research, scraping, and compendium generation platform combining **n8n workflows**, **Selenium headless browser automation**, and **ResearchForge** — an interactive autonomous AI agent studio with live terminal execution, human-in-the-loop chat corrections, domain filtering, and publication-ready multi-page PDF generation.

---

## 🌟 Key Highlights & Features

- **Autonomous Research & Scraping Agent**: Talk directly to the AI agent to assign scraping tasks, provide live corrections, filter tracks, and trigger automated extractions.
- **L&T Techgium Challenge Extractor**: Full automated extraction of all **60 official competition problem statements** across 9 engineering domains.
- **60+ Page PDF Compendium Generator**: Formats and compiles extracted problem statements into a publication-ready multi-page PDF with cover page, track summary statistics, index of challenges, and structured problem cards (Background, Challenge Statement, and Deliverables).
- **Session & 2FA Recovery**: Automatic browser session detection and interactive 6-digit OTP handling for portals with two-factor authentication.
- **Real-Time Live Terminal**: Watch every action, network request, and processing step inside the interactive Agent Studio.
- **n8n & Selenium Workflows**: Pre-configured n8n workflow nodes and Selenium containers for automated scheduled web extraction.

---

## 🏗️ Repository Architecture

```
.
├── ResearchForge/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── agent_engine.py       # Autonomous agent session, conversational loop & filtering
│   │   │   ├── techgium_adapter.py   # Portal authentication, OTP handling & session extraction
│   │   │   ├── pdf_generator.py      # ReportLab multi-page PDF compendium generator
│   │   │   ├── crawler.py            # Web scraping & content extraction
│   │   │   ├── searcher.py           # Multi-engine search provider
│   │   │   ├── ai_extractor.py       # Entity & problem statement AI extraction
│   │   │   └── main.py               # FastAPI REST endpoints
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── frontend/
│   │   ├── app/
│   │   │   ├── agent/                # AI Agent Studio (Live Terminal, Chat & Challenge Viewer)
│   │   │   ├── layout.js             # Global layout & navigation
│   │   │   └── page.js               # Research dashboard
│   │   └── package.json
│   ├── exports/                      # Generated PDF compendiums
│   ├── docker-compose.yml
│   └── .env.example
├── n8n-ultimate-scraper-main/
│   ├── extension/                    # Headless browser helper extensions
│   ├── Selenium_Ultimate_Scraper_Workflow.json  # Exported n8n workflow
│   └── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher (`npm` installed)
- **Docker** (optional, for containerized deployment)

---

### 2. Backend Setup (FastAPI & Agent Engine)

```bash
cd ResearchForge/backend

# Create virtual environment
python -m venv venv
# Activate on Windows:
venv\Scripts\activate
# Activate on Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the API server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The FastAPI backend will start at: `http://localhost:8001` (API docs at `http://localhost:8001/docs`).

---

### 3. Frontend Setup (Next.js Agent Studio)

```bash
cd ResearchForge/frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev -- -p 3001
```

Open the web interface in your browser:
👉 **`http://localhost:3001/agent`**

---

### 4. Running with Docker Compose

To run the complete stack with PostgreSQL and containerized services:

```bash
cd ResearchForge
docker-compose up -d
```

---

## 📊 Extracted Techgium Challenge Compendium

The included adapter extracts all 60 problem statements across:
- **Manufacturing** (20 challenges)
- **MedTech** (10 challenges)
- **Artificial Intelligence** (9 challenges)
- **Energy** (5 challenges)
- **Mobility** (4 challenges)
- **Digital Platforms** (4 challenges)
- **Cyber Security** (4 challenges)
- **Robotics & Autonomous Systems** (2 challenges)
- **Sustainability** (2 challenges)

Click **"Download PDF"** in the Agent Studio to download the complete 62-page document compiled by ReportLab.

---

## 🔒 Security & Privacy

- All secrets and personal credentials are read from environment variables (`.env`).
- Never commit active API tokens, passwords, or personal credentials to public repositories.
- Copy `.env.example` to `.env` and fill in your custom environment configurations.

---

## 📄 License

This repository is licensed under the [MIT License](LICENSE).
