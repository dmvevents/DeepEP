"""
Serializers for Tenant model
"""
from rest_framework import serializers
from .tenant import Tenant


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for Tenant theme configuration
    """
    theme_config = serializers.ReadOnlyField()

    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'slug',
            'logo_url',
            'primary_color',
            'secondary_color',
            'accent_color',
            'contact_email',
            'contact_phone',
            'website',
            'theme_config',
        ]
        read_only_fields = ['id', 'theme_config']
