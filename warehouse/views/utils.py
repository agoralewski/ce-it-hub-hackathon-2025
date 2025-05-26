"""
Utility functions for warehouse views.
"""

import socket
from django.conf import settings


def is_admin(user):
    """Check if user is a superuser (WH Administrator)"""
    return user.is_superuser


def get_network_ip():
    """Get the host machine's network IP address."""
    try:
        # This creates a socket that would connect to an external service
        # but doesn't actually establish a connection
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Using Google's DNS server as a dummy target
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to localhost if we can't determine the IP
        return '127.0.0.1'


def build_network_absolute_uri(request, path=None):
    """
    Build an absolute URI that uses the machine's network IP instead of localhost.

    Args:
        request: The HTTP request object
        path: The path to include in the URI

    Returns:
        str: The absolute URI with the network IP
    """
    # First, get the base absolute URI from the request
    absolute_uri = request.build_absolute_uri(path)

    # Check settings for a manually configured host
    network_host = getattr(settings, 'NETWORK_HOST', None)
    if not network_host:
        # Auto-detect the IP address
        network_host = get_network_ip()

    # Extract scheme, path, query from the original
    scheme_end = absolute_uri.find('://')
    if scheme_end > 0:
        scheme = absolute_uri[: scheme_end + 3]  # include '://'
        rest = absolute_uri[scheme_end + 3 :]

        # Find the end of the host part (could include port)
        host_end = rest.find('/')
        if host_end > 0:
            path_and_query = rest[host_end:]
            host_and_port = rest[:host_end]

            # Check if there's a port
            port = ''
            if ':' in host_and_port:
                port = ':' + host_and_port.split(':')[1]

            # Build the new URI with the network IP
            return f'{scheme}{network_host}{port}{path_and_query}'

    # If parsing failed, return the original
    return absolute_uri
