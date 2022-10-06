from rest_framework import authentication


class AnonCSRFSessionAuthentication(authentication.SessionAuthentication):
    """
    Enforce the CSRF checks even for non-authenticated users.

    DRF by default only enforces CSRF checks for authenticated users, assuming the
    attack vector targets logged-in sessions. However, non-authenticated user sessions
    also need CSRF-protection. Only legitimate users who have received the CSRF-token
    from an endpoint are allowed to consume the API using session cookies.
    """

    def authenticate(self, request):
        result = super().authenticate(request)
        # this is different from core DRF
        if result is None:
            self.enforce_csrf(request)
        return result
