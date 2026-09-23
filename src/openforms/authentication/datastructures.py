from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from openforms.accounts.models import User
from openforms.typing import JSONObject

from .constants import AuthAttribute
from .models import RegistratorInfo


@dataclass
class Registrator:
    """
    Abstraction on top of :class:`openforms.authentication.models.RegistratorInfo`.

    This datastructure handles the interoperability between raw ``RegistratorInfo``
    instances and it's relation to local user instances.
    """

    _wrapped_registrator_info: RegistratorInfo
    attribute: AuthAttribute
    value: str
    oidc_claims: JSONObject | None = None

    @classmethod
    def create_from(cls, registrator_info: RegistratorInfo) -> Self:
        oidc_claims: JSONObject | None = None

        # translate from local user ID to employee ID if possible
        match registrator_info.attribute:
            case AuthAttribute.local_user_id:
                user = User.objects.get(id=registrator_info.value)
                attribute = AuthAttribute.employee_id
                value = user.employee_id or user.username
                oidc_claims = user.raw_oidc_claims or None
            case _:  # pass through the rest
                attribute = registrator_info.attribute
                value = registrator_info.value

        return cls(
            _wrapped_registrator_info=registrator_info,
            attribute=attribute,
            value=value,
            oidc_claims=oidc_claims,
        )

    @property
    def plugin(self) -> str:
        return self._wrapped_registrator_info.plugin

    @property
    def attribute_hashed(self) -> bool:
        return self._wrapped_registrator_info.attribute_hashed

    def hash_identifying_attributes(self, delay=False):
        self._wrapped_registrator_info.hash_identifying_attributes(delay=delay)
