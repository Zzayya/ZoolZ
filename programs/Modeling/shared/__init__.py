#!/usr/bin/env python3
"""
Modeling Shared Utilities
Cookie cutter and stamp generation logic
"""

from .cookie_logic import (
    generate_cookie_cutter,
    extract_outline_data,
    extract_inner_details,
    generate_cookie_cutter_from_outline,
    generate_detail_stamp_from_outlines
)
from .stamp_logic import generate_stamp

__all__ = [
    'generate_cookie_cutter',
    'extract_outline_data',
    'extract_inner_details',
    'generate_cookie_cutter_from_outline',
    'generate_detail_stamp_from_outlines',
    'generate_stamp'
]
