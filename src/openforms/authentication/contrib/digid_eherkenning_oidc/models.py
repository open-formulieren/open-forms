from typing_extensions import deprecated


@deprecated("Left here because used in migrations.")
def get_default_scopes_eidas():
    """
    Returns the default scopes to request for OpenID Connect logins for eIDAS.
    """
    return ["openid", "profile"]


@deprecated("Left here because used in migrations.")
def get_default_scopes_eidas_company():
    """
    Returns the default scopes to request for OpenID Connect logins for eIDAS with
    company.
    """
    return ["openid", "profile", "legal"]
