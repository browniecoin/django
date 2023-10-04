from django.http import HttpResponseForbidden
from django.conf import settings

class WhitelistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_ips = getattr(settings, 'ALLOWED_IPS', [])
        remote_ip = request.META.get('REMOTE_ADDR')

        if remote_ip not in allowed_ips:
            return HttpResponseForbidden("Access Denied")

        return self.get_response(request)

# middleware.py
class CustomXFrameOptionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check the request's Referer (if needed) and set X-Frame-Options accordingly.
        # For example, to allow framing from 'https://example.com':
        if 'HTTP_REFERER' in request.META:
            referer = request.META['HTTP_REFERER']
            if 'example.com' in referer:
                response['X-Frame-Options'] = 'ALLOW-FROM https://example.com'

        return response
