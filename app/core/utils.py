"""
Utils functions for app.
"""


def check_email_and_name(email, name):
    """Validate that both email and name are provided."""
    if not email:
        raise ValueError("Email is required.")
    if not name:
        raise ValueError("Name is required.")
