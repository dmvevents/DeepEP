# P0 Runbook - Critical Operations Guide

> **Owner**: Company Owner
> **Last Updated**: 2025-11-10
> **Incident Response**: See below for escalation paths

---

## 🚨 Critical Incidents (P0)

### Definition
P0 incidents are service-impacting events affecting customers or core functionality:
- Complete service outage
- Data loss or corruption
- Security breach
- Payment/financial processing failure
- LLM API exhaustion causing cascading failures

---

## 📊 Observability Quick Reference

### Health Endpoints
```bash
# Backend API health
curl http://localhost:8000/api/health/

# Scraper service health
curl http://localhost:8001/health

# OCR service health
curl http://localhost:8003/health
```

### Key Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| API Response Time | >2s | Check DB connections, Redis |
| LLM Token Usage | >80% daily quota | Enable rate limits, circuit breaker |
| Error Rate | >5% | Check logs, recent deployments |
| Database Connections | >80% pool | Scale DB or connection pool |
| Redis Memory | >90% | Clear cache, scale Redis |

---

## 🔥 Common P0 Scenarios

### 1. Service Down

**Symptoms**: HTTP 502/503, containers not responding

**Diagnosis**:
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs backend --tail=100
docker-compose logs frontend --tail=100
docker-compose logs scraper --tail=100

# Check resource usage
docker stats
```

**Fix**:
```bash
# Restart affected service
docker-compose restart backend

# Full restart if needed
docker-compose down && docker-compose up -d

# Check database connectivity
docker-compose exec backend python manage.py check --database default
```

---

### 2. LLM API Rate Limit / Cost Overrun

**Symptoms**: 429 errors, high API costs, scraper failures

**Immediate Actions**:
1. Enable circuit breaker (prevents cascading failures):
   ```bash
   # In .env.scraper
   ENABLE_CIRCUIT_BREAKER=true
   CIRCUIT_BREAKER_THRESHOLD=10  # failures before breaking
   CIRCUIT_BREAKER_TIMEOUT=300    # 5 min cooldown

   docker-compose restart scraper
   ```

2. Check current usage:
   ```bash
   # View ScraperLog for token usage
   docker-compose exec backend python manage.py shell
   >>> from api.models import ScraperLog
   >>> ScraperLog.objects.filter(
   ...     started_at__date='2025-11-10'
   ... ).aggregate(total=models.Sum('tokens_used'))
   ```

3. Enable rate limiting (backend settings):
   ```python
   # config/settings.py
   REST_FRAMEWORK = {
       'DEFAULT_THROTTLE_RATES': {
           'anon': '50/hour',      # Reduce from 100
           'user': '500/hour',     # Reduce from 1000
       }
   }
   ```

**Prevention**:
- Set `SCRAPER_MAX_RETRIES=1` (reduce from 3)
- Monitor daily token budget
- Use cached tax data when available (30-day default)

---

### 3. Database Performance Degradation

**Symptoms**: Slow queries, timeouts, high CPU

**Diagnosis**:
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U admin -d mortgage_calc

# Check slow queries
SELECT pid, now() - query_start as duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

# Check database size
SELECT pg_size_pretty(pg_database_size('mortgage_calc'));
```

**Fix**:
```sql
-- Kill long-running query (if safe)
SELECT pg_terminate_backend(PID);

-- Reindex tables
REINDEX TABLE api_taxdata;
REINDEX TABLE api_loanestimate;
```

---

### 4. White-Label Theming Issues

**Symptoms**: UI shows default colors/logo, API errors

**Diagnosis**:
```bash
# Check feature flag
grep ENABLE_TENANT_THEMING .env

# Test tenant API
curl http://localhost:8000/api/tenants/current/
```

**Fix**:
```bash
# Enable feature flag
echo "ENABLE_TENANT_THEMING=true" >> .env
docker-compose restart backend

# Create default tenant (Django shell)
docker-compose exec backend python manage.py shell
>>> from api.tenant import Tenant
>>> Tenant.objects.create(
...     name='Default Company',
...     slug='default',
...     primary_color='#667eea',
...     is_active=True
... )
```

---

## 🛡️ Security Incidents

### Suspected Breach
1. **Immediately**: Rotate all secrets
   ```bash
   # Generate new Django secret
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

   # Update .env with new keys
   # Restart services
   docker-compose down && docker-compose up -d
   ```

2. Check audit logs:
   ```bash
   docker-compose exec backend python manage.py shell
   >>> from api.models import AuditEvent
   >>> AuditEvent.objects.filter(timestamp__gte='2025-11-10').count()
   ```

3. Review access logs (Nginx):
   ```bash
   docker-compose logs nginx | grep -E "401|403|500"
   ```

---

## 📞 Escalation

### Severity Levels

| Level | Response Time | Escalation |
|-------|---------------|------------|
| P0 (Critical) | Immediate | All hands, page on-call |
| P1 (High) | 30 minutes | Engineering lead |
| P2 (Medium) | 4 hours | Team triage |
| P3 (Low) | Next sprint | Backlog |

### Contact List
- **On-Call Engineer**: [Your contact]
- **DevOps**: [Your contact]
- **Security**: [Your contact]

---

## 🔍 Debugging Tips

### Enable Debug Mode (Non-Production Only)
```bash
# .env
DEBUG=True
LOG_LEVEL=DEBUG

docker-compose restart backend
```

### Check Redis Cache
```bash
docker-compose exec redis redis-cli

# List all keys
KEYS *

# Check memory usage
INFO memory

# Clear cache (if needed)
FLUSHDB
```

### View Celery Tasks
```bash
# List active tasks
docker-compose exec backend celery -A config inspect active

# Check worker status
docker-compose exec backend celery -A config inspect stats
```

---

## 💰 Cost Management

### LLM API Budget Alerts

Set up monitoring for:
1. **Daily token usage** > 80% quota
2. **Cost per scrape** > $0.50
3. **Failed scrapes** > 10% (wasted calls)

### Cost Optimization
- Enable `ENABLE_AUTO_RESCRAPE=False` to prevent automatic refreshes
- Use `SCRAPER_CACHE_EXPIRY_DAYS=90` (extend cache from 30 days)
- Batch county scrapes instead of on-demand

---

## 📈 Capacity Planning

### Scale Indicators

| Indicator | Threshold | Action |
|-----------|-----------|--------|
| Concurrent users | >100 | Add backend replicas |
| Loan estimates/day | >500 | Scale PostgreSQL |
| Scraper queue depth | >50 | Add Celery workers |

### Horizontal Scaling
```bash
# Scale backend
docker-compose up -d --scale backend=3

# Scale Celery workers
docker-compose up -d --scale celery=5
```

---

## ✅ Post-Incident Checklist

After resolving a P0:
- [ ] Document root cause
- [ ] Update this runbook with learnings
- [ ] Add monitoring/alerting to prevent recurrence
- [ ] Schedule blameless postmortem
- [ ] Communicate resolution to stakeholders

---

## 📚 Additional Resources

- [Architecture Docs](architecture/REPO_STRUCTURE.md)
- [Deployment Guide](deployment/DOCKER_OPERATIONS.md)
- [Debugging Guide](development/DEBUGGING_GUIDE.md)
- [API Reference](development/QUICK_REFERENCE.md)

---

**Remember**: Stay calm, follow the runbook, and document everything for post-incident review.
