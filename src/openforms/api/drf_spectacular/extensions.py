from drf_spectacular.authentication import SessionScheme


class AnonCSRFSessionScheme(SessionScheme):
    target_class = "openforms.api.authentication.AnonCSRFSessionAuthentication"
