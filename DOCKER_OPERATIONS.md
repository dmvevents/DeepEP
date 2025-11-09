# Docker Operations Guide

## Quick Reference

### Start All Services
```bash
docker-compose up -d
```

### Stop All Services (Keep Data)
```bash
docker-compose down
```

### Stop All Services (Remove Data)
```bash
docker-compose down -v
```

### View Running Containers
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f scraper-agent
docker-compose logs -f postgres
```

---

## Services Overview

The application consists of the following services:

### **Core Services**
1. **postgres** - PostgreSQL 15 database (port 5432)
2. **redis** - Redis cache and message broker (port 6379)
3. **backend** - Django REST API (port 8000)
4. **scraper-agent** - FastAPI scraper service (port 8001)
5. **celery** - Background task worker
6. **celery-beat** - Scheduled task scheduler

### **AI Services**
7. **ocr-service** - OCR processing with Ollama (port 8003)
8. **vlm-service** - Vision-Language Model service (port 8002)

---

## Common Operations

### 1. First Time Setup

```bash
# Build all images
docker-compose build

# Start services
docker-compose up -d

# Wait for database to be ready, then run migrations
docker-compose exec backend python manage.py migrate

# Load initial data (states and counties)
docker-compose exec backend python manage.py load_jurisdictions

# Create admin user
docker-compose exec backend python manage.py createsuperuser
```

### 2. Daily Development

```bash
# Start everything
docker-compose up -d

# Stop everything when done
docker-compose down
```

### 3. Restart Specific Service

```bash
docker-compose restart backend
docker-compose restart scraper-agent
```

### 4. Rebuild After Code Changes

```bash
# Rebuild and restart specific service
docker-compose up -d --build backend

# Rebuild all services
docker-compose build
docker-compose up -d
```

### 5. Database Operations

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U admin -d mortgage_calc

# Backup database
docker-compose exec postgres pg_dump -U admin mortgage_calc > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U admin mortgage_calc

# Run Django migrations
docker-compose exec backend python manage.py migrate

# Create migration
docker-compose exec backend python manage.py makemigrations
```

### 6. Access Container Shell

```bash
# Backend Django shell
docker-compose exec backend python manage.py shell

# Backend bash shell
docker-compose exec backend bash

# Postgres shell
docker-compose exec postgres psql -U admin -d mortgage_calc

# Redis CLI
docker-compose exec redis redis-cli
```

### 7. View Service Status

```bash
# Check health status
docker-compose ps

# Check resource usage
docker stats

# Check specific service logs
docker-compose logs --tail=100 backend
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check for port conflicts
lsof -i :8000  # Backend
lsof -i :8001  # Scraper
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill conflicting processes if needed
kill -9 <PID>

# Remove old containers and restart
docker-compose down
docker-compose up -d
```

### Database Connection Issues

```bash
# Check if database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Verify database exists
docker-compose exec postgres psql -U admin -l
```

### Backend Unhealthy

```bash
# Check logs
docker-compose logs backend

# Verify migrations are applied
docker-compose exec backend python manage.py showmigrations

# Run migrations
docker-compose exec backend python manage.py migrate

# Restart service
docker-compose restart backend
```

### Scraper Service Issues

```bash
# Check logs
docker-compose logs scraper-agent

# Verify environment variables
docker-compose exec scraper-agent env | grep -E "(LLM|API)"

# Test manually
curl http://localhost:8001/health
```

### Clear Everything and Start Fresh

```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove any orphaned containers
docker container prune -f

# Rebuild and start
docker-compose build --no-cache
docker-compose up -d

# Re-initialize database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py load_jurisdictions
docker-compose exec backend python manage.py createsuperuser
```

---

## Environment Variables

Key environment variables are set in:
- `.env` - Backend Django settings
- `.env.scraper` - Scraper service settings

Required variables:
```bash
# Backend (.env)
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://admin:password@postgres:5432/mortgage_calc
REDIS_URL=redis://redis:6379/0

# Scraper (.env.scraper)
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
DATABASE_URL=postgresql://admin:password@postgres:5432/mortgage_calc
```

---

## Health Checks

Services include health checks:

```bash
# Backend
curl http://localhost:8000/health

# Scraper
curl http://localhost:8001/health

# OCR Service
curl http://localhost:8003/health

# Database
docker-compose exec postgres pg_isready -U admin

# Redis
docker-compose exec redis redis-cli ping
```

---

## Data Persistence

Data is persisted in Docker volumes:

- `postgres_data` - Database data
- `redis_data` - Redis data

To remove all data:
```bash
docker-compose down -v
```

To backup data:
```bash
# Backup database
docker run --rm \
  -v real_estate_app_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz -C /data .
```

---

## Production Deployment

For production:

1. Set `DEBUG=False` in `.env`
2. Use strong `SECRET_KEY`
3. Configure proper `ALLOWED_HOSTS`
4. Use production-grade database
5. Set up SSL/TLS certificates
6. Configure monitoring and logging
7. Set up automated backups

```bash
# Production startup
docker-compose -f docker-compose.prod.yml up -d
```

---

## Maintenance Commands

```bash
# Clean up unused Docker resources
docker system prune -a

# View disk usage
docker system df

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

---

## Quick Start Commands

```bash
# Start everything
make up

# Stop everything
make down

# View logs
make logs

# Restart a service
make restart service=backend
```

---

## Support

For issues or questions:
- Check logs: `docker-compose logs -f [service]`
- Review documentation: `CLAUDE.md`
- Check environment variables
- Verify network connectivity

---

## Service URLs

- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Scraper API**: http://localhost:8001
- **VLM Service**: http://localhost:8002
- **OCR Service**: http://localhost:8003
- **Frontend** (dev): http://localhost:5173
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
