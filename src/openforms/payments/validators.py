from collections.abc import Sequence

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext as _


@deconstructible
class IdTemplateValidator:
    def __init__(
        self,
        allowed_groups: Sequence[str] = (
            "{year}",
            "{public_reference}",
            "{uid}",
            "/",
            ".",
            "_",
            "-",
        ),
    ):
        self.allowed_groups = allowed_groups

    def __call__(
        self,
        value: str,
    ) -> None:
        if "{uid}" not in value:
            raise ValidationError(_("The template must include the {uid} placeholder."))

        for allowed in self.allowed_groups:
            value = value.replace(allowed, "")

        if value and not value.isalnum():
            raise ValidationError(
                _(
                    "The template may only consist of alphanumeric and allowed groups "
                    "of characters: %(groups)s"
                )
                % {"groups": ", ".join(self.allowed_groups)}
            )
