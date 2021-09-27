import logging

from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist

from mozilla_django_oidc.auth import (
    OIDCAuthenticationBackend as _OIDCAuthenticationBackend,
)

from .mixins import SoloConfigMixin
from .models import OpenIDConnectConfig

logger = logging.getLogger(__name__)


class OIDCAuthenticationBackend(SoloConfigMixin, _OIDCAuthenticationBackend):
    """
    Modifies the default OIDCAuthenticationBackend to use the `sub` claim
    as unique identifier.
    """

    def __init__(self, *args, **kwargs):
        self.config = OpenIDConnectConfig.get_solo()

        if not self.config.enabled:
            return

        super().__init__(*args, **kwargs)

    def authenticate(self, *args, **kwargs):
        if not self.config.enabled:
            return None

        return super().authenticate(*args, **kwargs)

    def get_user_instance_values(self, claims):
        """
        Map the names and values of the claims to the fields of the User model
        """
        return {
            model_field: claims.get(claims_field, "")
            for model_field, claims_field in self.config.claim_mapping.items()
        }

    def create_user(self, claims):
        """Return object for a newly created user account."""
        sub = claims.get("sub")

        logger.debug("Creating OIDC user: %s", sub)

        user = self.UserModel.objects.create_user(
            **{self.UserModel.USERNAME_FIELD: sub}
        )
        self.update_user(user, claims)

        return user

    def filter_users_by_claims(self, claims):
        """Return all users matching the specified subject."""
        sub = claims.get("sub")

        if not sub:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(username__iexact=sub)

    def verify_claims(self, claims):
        """Verify the provided claims to decide if authentication should be allowed."""
        scopes = self.get_settings("OIDC_RP_SCOPES", "openid email")

        logger.debug("OIDC claims received: %s", claims)

        if "sub" not in claims:
            logger.error("`sub` not in OIDC claims, cannot proceed with authentication")
            return False
        return True

    def update_user(self, user, claims):
        """Update existing user with new claims, if necessary save, and return user"""
        values = self.get_user_instance_values(claims)
        for field, value in values.items():
            setattr(user, field, value)
        logger.debug("Updating OIDC user %s with: %s", user, values)

        # Users can only be promoted to staff. Staff rights are never taken by OIDC.
        if self.config.make_users_staff and not user.is_staff:
            user.is_staff = True
            user.save(update_fields=["is_staff"])

        user.save(update_fields=values.keys())

        self.update_user_groups(user, claims)

        return user

    def update_user_groups(self, user, claims):
        """
        Updates user group memberships based on the group_claim setting.

        Copied and modified from: https://github.com/snok/django-auth-adfs/blob/master/django_auth_adfs/backend.py
        """
        groups_claim = self.config.groups_claim

        if groups_claim:
            # Update the user's group memberships
            django_groups = [group.name for group in user.groups.all()]

            if groups_claim in claims:
                claim_groups = claims[groups_claim]
                if not isinstance(claim_groups, list):
                    claim_groups = [
                        claim_groups,
                    ]
            else:
                logger.debug(
                    "The configured groups claim '%s' was not found in the access token",
                    groups_claim,
                )
                claim_groups = []
            if sorted(claim_groups) != sorted(django_groups):
                existing_groups = list(
                    Group.objects.filter(name__in=claim_groups).iterator()
                )
                existing_group_names = frozenset(
                    group.name for group in existing_groups
                )
                new_groups = []
                if self.config.sync_groups:
                    new_groups = [
                        Group.objects.get_or_create(name=name)[0]
                        for name in claim_groups
                        if name not in existing_group_names
                    ]
                else:
                    for name in claim_groups:
                        if name not in existing_group_names:
                            try:
                                group = Group.objects.get(name=name)
                                new_groups.append(group)
                            except ObjectDoesNotExist:
                                pass
                user.groups.set(existing_groups + new_groups)
