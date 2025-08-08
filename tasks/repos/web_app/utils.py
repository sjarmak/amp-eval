"""Utility functions that create circular imports."""
from .models import User  # Circular import with models.py


def format_username(username):
    """Format username - should be in user service."""
    return username.lower().strip()


def get_user_profile(user_id):
    """Get user profile - creates circular import."""
    try:
        user = User.objects.get(id=user_id)  # Imports models
        return user.get_profile_data()
    except User.DoesNotExist:
        return {'error': 'User not found'}


def validate_email(email):
    """Email validation that should be in email service."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
