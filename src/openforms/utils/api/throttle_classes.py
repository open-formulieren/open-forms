from rest_framework.throttling import UserRateThrottle


class PollingRateThrottle(UserRateThrottle):
    scope = "polling"

    def allow_request(self, request, view):
        if request.user.is_authenticated and request.user.is_staff:
            # unlimited for admin users
            return True
        else:
            # regular user-rate under our own scope
            return super().allow_request(request, view)
