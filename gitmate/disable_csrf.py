from django.utils.deprecation import MiddlewareMixin


class DisableCSRFMiddleware(MiddlewareMixin):  # pragma: no cover
    def process_request(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)
