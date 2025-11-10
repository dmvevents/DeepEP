# Real Estate Mortgage Calculator

> AI-Powered Mortgage Calculation Platform with Automated Tax Data Collection

[![Status](https://img.shields.io/badge/status-beta-yellow)](https://github.com)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![React](https://img.shields.io/badge/react-19.2-blue)](https://reactjs.org)

---

## 🚀 Quick Start

```bash
# Start all services with Docker
docker-compose up -d

# Access the application
open http://localhost:3000
```

**Demo Accounts:**
- Admin: `admin` / `admin`
- Customer: `demo` / `demo123`

**Full setup instructions**: See [Quick Start Guide](docs/development/QUICKSTART.md)

---

## 🎯 What is This?

An intelligent mortgage calculator that automatically collects tax data from all 50 US states using AI and provides CFPB-compliant loan estimates with 98% accuracy.

### Key Features

- **🤖 Automated Tax Data**: AI scrapes property tax, transfer fees, and recordation taxes from official government sources
- **📊 CFPB Compliant**: Complete federal Loan Estimate calculations
- **🗺️ National Coverage**: All 50 states, 3,143+ counties
- **⚡ Real-Time**: Instant mortgage calculations
- **👥 Full Workflow**: Application submission through admin approval
- **📄 Smart OCR**: AI-powered document processing

---

## 📚 Documentation

### Get Started
- **[Quick Start](docs/development/QUICKSTART.md)** - Up and running in 5 minutes
- **[Docker Operations](docs/deployment/DOCKER_OPERATIONS.md)** - Managing containers
- **[API Reference](docs/development/QUICK_REFERENCE.md)** - API endpoints

### For Developers
- **[Development Guide](docs/development/CLAUDE.md)** - Complete dev setup
- **[Architecture](docs/architecture/REPO_STRUCTURE.md)** - System design
- **[Debugging Guide](docs/development/DEBUGGING_GUIDE.md)** - Troubleshooting

### For Stakeholders
- **[Project Status Report](docs/summaries/PROJECT_STATUS_REPORT.md)** - Progress and roadmap
- **[Implementation Summary](docs/summaries/IMPLEMENTATION_SUMMARY.md)** - Recent updates

### Technical Specs
- **[Tax Data Schema](docs/specifications/ENHANCED_TAX_DATA_SCHEMA.md)** - Data structure
- **[Test Results](docs/summaries/TEST_SUMMARY.md)** - Testing status

---

## 🏗️ Architecture

```
Frontend (React)  →  Backend API (Django)  →  PostgreSQL
                  →  Scraper (FastAPI)     →  Redis
                  →  OCR Service          →  Celery
                  →  VLM Service
```

**Tech Stack:**
- Backend: Django 4.2, FastAPI, PostgreSQL 15, Redis 7, Celery
- AI: OpenAI GPT-4 / Claude 3.5, Ollama
- Frontend: React 19.2, TypeScript 5.6, Material-UI 5.18
- Infrastructure: Docker Compose, Nginx

---

## 📊 Current Status

**Version:** v2.0-beta  
**Progress:** 85% Complete  
**Status:** Ready for Beta Testing  

### ✅ Completed
- Core mortgage calculator (CFPB compliant)
- AI tax data scraper (all 50 states)
- Enhanced tax schema v2.0 (98% accuracy)
- User authentication & workflow
- Admin dashboard
- React frontend
- Document OCR
- Docker deployment

### 🚧 In Progress
- Enhanced tax proration
- RESPA escrow calculations
- Multi-county testing
- Email notifications

See full status in [Project Status Report](docs/summaries/PROJECT_STATUS_REPORT.md)

---

## 🔧 Configuration

```bash
# 1. Copy environment templates
cp .env.example .env
cp .env.scraper.example .env.scraper

# 2. Add API keys to .env.scraper
OPENAI_API_KEY=your-key-here
SERP_API_KEY=your-key-here

# 3. Start services
docker-compose up -d

# 4. Initialize database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_jurisdictions
docker-compose exec backend python manage.py createsuperuser
```

---

## 📁 Project Structure

```
real_estate_app/
├── backend/              # Django REST API
├── frontend-react/       # React application
├── scraper/             # Tax data scraper
├── ocr-service/         # Document OCR
├── vlm-service/         # Vision-language model
├── nginx/               # Reverse proxy
├── docs/                # Documentation
│   ├── architecture/    # System design
│   ├── deployment/      # Ops guides
│   ├── development/     # Dev guides
│   ├── specifications/  # Technical specs
│   └── summaries/       # Status reports
├── tests/               # Test suites
└── docker-compose.yml   # Container config
```

---

## 🔗 Quick Links

- **[Documentation Index](docs/README.md)** - All documentation
- **[Quick Start](docs/development/QUICKSTART.md)** - Get started fast
- **[API Docs](http://localhost:8000/api/docs)** - Interactive API (when running)
- **[Project Status](docs/summaries/PROJECT_STATUS_REPORT.md)** - Current progress

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/real_estate_app/issues)
- **Docs**: See `/docs` directory
- **Guides**: [Quick Reference](docs/development/QUICK_REFERENCE.md)

---

**Built by Anton Alexander** | Last Updated: November 9, 2025
