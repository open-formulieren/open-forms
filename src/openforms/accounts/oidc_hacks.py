from typing import override

from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.plugins import OIDCAdminPlugin
from mozilla_django_oidc_db.registry import register

from .models import User


class CustomOIDCAdminPlugin(OIDCAdminPlugin):
    @override
    def update_user(self, user, claims):
        user = super().update_user(user, claims)
        assert isinstance(user, User)
        user.raw_oidc_claims = claims
        user.save(update_fields=("raw_oidc_claims",))
        return user


def replace_builtin_admin_plugin():

    # unregister the existing plugin so that we can register our override
    del register._registry[OIDC_ADMIN_CONFIG_IDENTIFIER]

    # replaces the default admin plugin to be able to store the raw OIDC claims on the
    # user model
    register(OIDC_ADMIN_CONFIG_IDENTIFIER)(CustomOIDCAdminPlugin)
