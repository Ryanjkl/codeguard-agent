"""Utility functions - contains maintainability issues."""

import os
import json


# ISSUE: Mutable global state
_global_cache = {}


def load_config(config_path: str = "config.json"):
    """Load configuration from file."""
    with open(config_path) as f:
        return json.load(f)


def validate_email(email: str) -> bool:
    """Check if email is valid."""
    # Simple regex approach
    import re
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def format_date(date_obj):
    """Format a date object to string."""
    # ISSUE: No type checking, could crash
    return date_obj.strftime("%Y-%m-%d")


def get_cached_value(key, data={}):  # ISSUE: Mutable default argument
    """Fetch from cache or compute."""
    if key in data:
        return data[key]
    # Could add compute logic
    return data.get(key)


def complex_calculation(x, y, z, a, b, c):  # ISSUE: Too many parameters
    """A function that does too many things."""
    result = 0

    if x > 0:
        if y > 0:
            if z > 0:
                if a > 0:
                    # ISSUE: Deep nesting (level 4)
                    if b > 0:
                        if c > 0:
                            result = x + y + z + a + b + c

    try:
        return result / (x - y)
    except:
        # ISSUE: Bare except
        return 0


# TODO: Add async versions of these utilities
# FIXME: Cache eviction not implemented
# HACK: Using global state for cache
