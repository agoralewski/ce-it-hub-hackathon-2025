# settings.py helper to load environment variables
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def get_env_variable(var_name, default=None):
    """Get environment variable or return default value"""
    return os.environ.get(var_name, default)


def get_bool_env_variable(var_name, default=False):
    """Get boolean environment variable or return default value"""
    value = get_env_variable(var_name, default)
    if isinstance(value, bool):
        return value
    return value.lower() in ('true', '1', 't', 'y', 'yes')
