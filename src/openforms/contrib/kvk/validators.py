from functools import partial
from typing import Literal

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from requests import RequestException

from openforms.typing import StrOrPromise
from openforms.utils.validators import validate_digits, validate_rsin
from openforms.validations.base import BasePlugin
from openforms.validations.registry import register

from .client import NoServiceConfigured, SearchParams, get_kvk_search_client

KVK_LOOKUP_CACHE_TIMEOUT = 5 * 60


@deconstructible
class NumericBaseValidator:
    value_size: int
    value_label: StrOrPromise
    error_messages = {
        "too_short": _("%(type)s should have %(size)i characters."),
    }

    def __call__(self, value: str):
        validate_digits(value)

        if len(value) != self.value_size:
            raise ValidationError(
                self.error_messages["too_short"],
                params={"size": self.value_size, "type": self.value_label},
                code="invalid",
            )


@deconstructible
class KVKNumberValidator(NumericBaseValidator):
    value_size = 8
    value_label = _("KvK number")


@deconstructible
class KVKBranchNumberValidator(NumericBaseValidator):
    value_size = 12
    value_label = _("Branch number")


validate_kvk = KVKNumberValidator()
validate_branchNumber = KVKBranchNumberValidator()


def get_kvk_search_results(query: SearchParams) -> dict:
    with get_kvk_search_client() as client:
        result = client.get_search_results(query_params=query)
        return result


class KVKRemoteValidatorMixin:
    query_param: Literal["kvkNummer", "rsin", "vestigingsnummer"]
    value_label: StrOrPromise

    error_messages = {
        "not_found": _("%(type)s does not exist."),
        "too_short": _("%(type)s should have %(size)i characters."),
    }

    def validate(self, value: str) -> bool:
        assert self.query_param
        query: SearchParams = {}
        query[self.query_param] = value

        try:
            result = cache.get_or_set(
                key=f"KVK|get_search_results|{self.query_param}:{value}",
                default=partial(get_kvk_search_results, query),
                timeout=KVK_LOOKUP_CACHE_TIMEOUT,
            )
        except (RequestException, NoServiceConfigured):
            raise ValidationError(
                self.error_messages["not_found"],
                params={"type": self.value_label},
                code="invalid",
            )

        if not len(result.get("resultaten", [])):
            raise ValidationError(
                self.error_messages["not_found"],
                params={"type": self.value_label},
                code="invalid",
            )

        return True


@register("kvk-kvkNumber")
@deconstructible
class KVKNumberRemoteValidator(KVKRemoteValidatorMixin, BasePlugin[str]):
    query_param = "kvkNummer"
    value_label = _("KvK number")

    verbose_name = _("KvK number")
    for_components = ("textfield",)

    def __call__(self, value: str, submission):
        validate_kvk(value)
        self.validate(value)


@register("kvk-rsin")
@deconstructible
class KVKRSINRemoteValidator(KVKRemoteValidatorMixin, BasePlugin[str]):
    query_param = "rsin"
    value_label = _("RSIN")

    verbose_name = _("KvK RSIN")
    for_components = ("textfield",)

    def __call__(self, value: str, submission):
        validate_rsin(value)
        self.validate(value)


@register("kvk-branchNumber")
@deconstructible
class KVKBranchNumberRemoteValidator(KVKRemoteValidatorMixin, BasePlugin[str]):
    query_param = "vestigingsnummer"
    value_label = _("Branch number")

    verbose_name = _("KvK branch number")
    for_components = ("textfield",)

    def __call__(self, value: str, submission):
        validate_branchNumber(value)
        self.validate(value)
