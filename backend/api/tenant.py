"""
Tenant model for white-label theming support
"""
from django.db import models
from django.core.validators import RegexValidator


class Tenant(models.Model):
    """
    Tenant model for multi-tenant white-label support.
    Stores branding configuration (logo, colors) for report customization.
    """
    # Tenant identity
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Tenant name (e.g., 'ABC Mortgage Co.')"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-safe identifier"
    )

    # Active status
    is_active = models.BooleanField(
        default=True,
        help_text="Tenant is active and can be used"
    )

    # Branding: Logo
    logo_url = models.URLField(
        blank=True,
        max_length=500,
        help_text="URL to tenant logo image (for reports and UI)"
    )
    logo_base64 = models.TextField(
        blank=True,
        help_text="Base64-encoded logo for embedded PDF reports"
    )

    # Branding: Colors (hex format)
    color_validator = RegexValidator(
        regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
        message='Color must be a valid hex code (e.g., #667eea)'
    )

    primary_color = models.CharField(
        max_length=7,
        default='#667eea',
        validators=[color_validator],
        help_text="Primary brand color (hex format)"
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#10b981',
        validators=[color_validator],
        help_text="Secondary brand color (hex format)"
    )
    accent_color = models.CharField(
        max_length=7,
        default='#764ba2',
        validators=[color_validator],
        help_text="Accent color for highlights (hex format)"
    )

    # Contact Information (for reports)
    contact_email = models.EmailField(
        blank=True,
        help_text="Tenant contact email (shown on reports)"
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Tenant contact phone (shown on reports)"
    )
    website = models.URLField(
        blank=True,
        max_length=200,
        help_text="Tenant website URL"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"

    @property
    def theme_config(self):
        """Return theme configuration as dict for frontend"""
        return {
            'name': self.name,
            'slug': self.slug,
            'logo_url': self.logo_url,
            'colors': {
                'primary': self.primary_color,
                'secondary': self.secondary_color,
                'accent': self.accent_color,
            },
            'contact': {
                'email': self.contact_email,
                'phone': self.contact_phone,
                'website': self.website,
            }
        }
