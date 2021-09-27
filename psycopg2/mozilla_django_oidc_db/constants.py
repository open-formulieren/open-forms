# Mapping the configuration model fieldnames for endpoints to their
# corresponding names in the OIDC spec
OIDC_MAPPING = {
    "oidc_op_authorization_endpoint": "authorization_endpoint",
    "oidc_op_token_endpoint": "token_endpoint",
    "oidc_op_user_endpoint": "userinfo_endpoint",
    "oidc_op_jwks_endpoint": "jwks_uri",
}

OPEN_ID_CONFIG_PATH = ".well-known/openid-configuration"
