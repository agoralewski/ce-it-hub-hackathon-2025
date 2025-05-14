"""
Utility functions for warehouse views.
"""

def is_admin(user):
    """Check if user is a superuser (WH Administrator)"""
    return user.is_superuser