# Tenant Theming (White-Label Support)

> **Phase**: Phase 4 - White-Label
> **Status**: ✅ Implemented
> **Feature Flag**: `ENABLE_TENANT_THEMING`

---

## Overview

Tenant theming enables white-label customization, allowing each tenant to configure:
- **Brand colors** (primary, secondary, accent)
- **Company logo** (URL or base64)
- **Contact information** (email, phone, website)

All UI elements and PDF reports automatically use tenant branding.

---

## Quick Start

### 1. Enable Feature Flag

```bash
# .env
ENABLE_TENANT_THEMING=true
```

Restart backend:
```bash
docker-compose restart backend
```

### 2. Create Tenant

```python
# Django shell
docker-compose exec backend python manage.py shell

from api.tenant import Tenant

tenant = Tenant.objects.create(
    name='ABC Mortgage Co.',
    slug='abc-mortgage',
    primary_color='#3b82f6',    # Blue
    secondary_color='#10b981',  # Green
    accent_color='#8b5cf6',     # Purple
    logo_url='https://example.com/logo.png',
    contact_email='info@abcmortgage.com',
    contact_phone='555-0123',
    website='https://abcmortgage.com',
    is_active=True
)
```

### 3. Test Theme

```bash
# Fetch current theme
curl http://localhost:8000/api/tenants/current/

# Expected response:
{
  "name": "ABC Mortgage Co.",
  "slug": "abc-mortgage",
  "logo_url": "https://example.com/logo.png",
  "colors": {
    "primary": "#3b82f6",
    "secondary": "#10b981",
    "accent": "#8b5cf6"
  },
  "contact": {
    "email": "info@abcmortgage.com",
    "phone": "555-0123",
    "website": "https://abcmortgage.com"
  }
}
```

---

## Architecture

### Backend

**Model**: `backend/api/tenant.py`
- Stores tenant configuration
- Validates hex color codes
- Provides `theme_config` property

**API**: `backend/api/views_tenant.py`
- `GET /api/tenants/current/` - Get active tenant theme
- `GET /api/tenants/` - List all tenants (admin)
- `GET /api/tenants/{slug}/` - Get specific tenant

### Frontend

**Context**: `frontend-react/src/contexts/TenantThemeContext.tsx`
- Fetches tenant theme on app load
- Provides `useTenantTheme()` hook
- Falls back to default theme on error

**Integration**: `frontend-react/src/App.tsx`
- Wraps app in `TenantThemeProvider`
- Creates MUI theme from tenant colors
- Auto-applies to all components

**PDF Export**: `frontend-react/src/pages/ScenarioDesk.tsx`
- Watermark uses tenant primary color
- Includes tenant logo (if configured)
- Branded report headers

---

## Feature Flag Behavior

| Flag State | Behavior |
|------------|----------|
| `ENABLE_TENANT_THEMING=false` | Uses default theme (hardcoded colors) |
| `ENABLE_TENANT_THEMING=true` | Loads tenant from database |
| No tenants exist | Falls back to default theme |

**Safe Rollback**: Disable flag to instantly revert to default theme (no code changes needed).

---

## Production Considerations

### Multi-Tenant Routing

Current implementation returns first active tenant. For production, implement:

1. **Subdomain routing**: `tenant1.yourdomain.com` → Tenant 1
2. **Custom domains**: `www.abcmortgage.com` → Tenant ABC
3. **User-based**: Assign users to tenants

Example tenant resolution:
```python
# views_tenant.py - current() method
def get_tenant_from_request(request):
    # Method 1: Subdomain
    subdomain = request.get_host().split('.')[0]
    tenant = Tenant.objects.filter(slug=subdomain, is_active=True).first()

    # Method 2: Custom domain
    if not tenant:
        domain = request.get_host()
        tenant = Tenant.objects.filter(custom_domain=domain, is_active=True).first()

    # Method 3: User assignment
    if not tenant and request.user.is_authenticated:
        tenant = request.user.profile.tenant

    return tenant
```

### Logo Hosting

**Options**:
1. **External URL**: `logo_url='https://cdn.example.com/logo.png'`
   - Pros: Fast CDN delivery
   - Cons: External dependency

2. **Base64 embedded**: `logo_base64='data:image/png;base64,...'`
   - Pros: Self-contained, works offline
   - Cons: Larger database size

3. **S3/Cloud Storage**: Upload to AWS S3, store URL
   - Pros: Scalable, secure
   - Cons: Requires S3 setup

### Rate Limiting

Tenant API is public (`AllowAny`). For production, consider:
```python
# Add caching
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache 15 minutes
def current(self, request):
    ...
```

---

## Cost & Performance

### Minimal Impact
- **Backend**: 1 extra DB query per page load (cached)
- **Frontend**: ~2KB theme context overhead
- **PDF**: No performance impact

### Circuit Breaker
Not needed - no external API calls. Theme data served from database.

---

## Testing

### Manual Test
1. Enable feature flag
2. Create tenant with custom colors
3. Visit app → UI should use new colors
4. Export PDF from Scenario Desk → PDF should have branded watermark

### Automated Tests (TODO)
```python
# tests/test_tenant.py
def test_tenant_theme_api():
    tenant = Tenant.objects.create(...)
    response = client.get('/api/tenants/current/')
    assert response.data['colors']['primary'] == '#3b82f6'
```

---

## Troubleshooting

**Issue**: UI shows default colors despite tenant existing

**Fix**:
1. Check feature flag: `grep ENABLE_TENANT_THEMING .env`
2. Verify tenant is active: `tenant.is_active = True`
3. Check browser console for API errors
4. Clear browser cache

**Issue**: PDF export missing logo

**Fix**:
1. Verify `logo_url` is publicly accessible
2. Check CORS headers if cross-origin
3. Use base64 logo for guaranteed availability

---

## Future Enhancements

- [ ] Custom fonts per tenant
- [ ] Multiple logo variants (light/dark mode)
- [ ] Tenant-specific email templates
- [ ] White-label mobile app support
- [ ] Tenant analytics dashboard

---

## Related Docs

- [RUNBOOK_P0.md](../RUNBOOK_P0.md) - Operations guide
- [Feature Flags](../../backend/config/settings.py) - All feature flags
- [API Reference](../development/QUICK_REFERENCE.md) - API endpoints

---

**Last Updated**: 2025-11-10 by Company Owner
