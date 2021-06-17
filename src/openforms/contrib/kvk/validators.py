from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

from requests import RequestException
from zds_client import ClientError

from openforms.contrib.kvk.client import KVKClient, KVKClientError
from openforms.utils.validators import validate_digits, validate_rsin
from openforms.validations.registry import register


@deconstructible
class NumericBaseValidator:
    value_size: int = NotImplemented
    value_label: str = NotImplemented
    error_messages = {
        "too_short": _("%(type)s should have %(size)i characters."),
    }

    def __call__(self, value):
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
    value_label = _("KVK number")


@deconstructible
class KVKBranchNumberValidator(NumericBaseValidator):
    value_size = 12
    value_label = _("Branch number")


validate_kvk = KVKNumberValidator()
validate_branchNumber = KVKBranchNumberValidator()


class KVKRemoteBaseValidator:
    query_param = NotImplemented
    value_label = NotImplemented

    error_messages = {
        "not_found": _("%(type)s does not exist."),
        "too_short": _("%(type)s should have %(size)i characters."),
    }

    def __call__(self, value):
        assert self.query_param

        client = KVKClient()
        try:
            result = client.query(**{self.query_param: value})
        except (RequestException, ClientError, KVKClientError):
            raise ValidationError(
                self.error_messages["not_found"],
                params={"type": self.value_label},
                code="invalid",
            )
        else:
            if not len(result["data"]["items"]):
                raise ValidationError(
                    self.error_messages["not_found"],
                    params={"type": self.value_label},
                    code="invalid",
                )
            else:
                return True


@register("kvk-kvkNumber", verbose_name=_("KVK Number"))
@deconstructible
class KVKNumberRemoteValidator(KVKRemoteBaseValidator):
    query_param = "kvkNumber"
    value_label = _("KVK number")

    def __call__(self, value):
        validate_kvk(value)
        super().__call__(value)


@register("kvk-rsin", verbose_name=_("KVK RSIN"))
@deconstructible
class KVKRSINRemoteValidator(KVKRemoteBaseValidator):
    query_param = "rsin"
    value_label = _("RSIN")

    def __call__(self, value):
        validate_rsin(value)
        super().__call__(value)


@register("kvk-branchNumber", verbose_name=_("KVK Branch Number"))
@deconstructible
class KVKBranchNumberRemoteValidator(KVKRemoteBaseValidator):
    query_param = "branchNumber"
    value_label = _("Branch number")

    def __call__(self, value):
        validate_branchNumber(value)
        super().__call__(value)
