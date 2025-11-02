"""
CSRF Exempt Middleware for API endpoints

API 엔드포인트는 CSRF 검증을 우회합니다.
"""

from django.utils.deprecation import MiddlewareMixin


class CSRFExemptAPIMiddleware(MiddlewareMixin):
    """
    /api/ 경로의 모든 요청에서 CSRF 검증을 우회합니다.
    """
    
    def process_request(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None
