from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """
    Sends the Content-Security-Policy header built from `SECURE_CSP`. Django 6 has this built in, with the same
    setting: after upgrading, `django.middleware.csp.ContentSecurityPolicyMiddleware` replaces this class.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if settings.SECURE_CSP:
            policy = '; '.join(f'{directive} {" ".join(sources)}' for directive, sources in settings.SECURE_CSP.items())
            # Like Django's, it leaves alone a policy that a view has already set
            response.headers.setdefault('Content-Security-Policy', policy)
        return response
