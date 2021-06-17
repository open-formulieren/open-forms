from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import ugettext_lazy as _

from openforms.utils.validators import validate_digits


@deconstructible
class KVKValidator:
    value_size = 8
    error_messages = {
        "too_short": _("KvK number should have %(size)i characters."),
    }

    def __call__(self, value):
        validate_digits(value)

        if len(value) != self.value_size:
            raise ValidationError(
                self.error_messages["too_short"],
                params={"size": self.value_size},
                code="invalid",
            )


validate_kvk = KVKValidator()
