"""
Lending Guidelines Module

Contains guideline-specific logic for:
- Fannie Mae (Conventional)
- Freddie Mac (Conventional)
- FHA (Government)
- USDA (Rural Housing)
- VA (Veterans)
- MGIC (Mortgage Insurance)
"""

from .base import BaseGuideline
from .fannie_mae import FannieMaeGuideline
from .fha import FHAGuideline
from .va import VAGuideline

__all__ = [
    'BaseGuideline',
    'FannieMaeGuideline',
    'FHAGuideline',
    'VAGuideline',
]
