from collections.abc import Collection, Iterator
from typing import ClassVar

from django.core.exceptions import ValidationError
from django.template import TemplateSyntaxError
from django.template.base import Lexer, TokenType
from django.utils.deconstruct import deconstructible
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _

from . import parse


@deconstructible
class DjangoTemplateValidator:
    """
    Validate template code to be a valid Django template.

    This validator ensures that the template is syntactically correct. Additionally,
    it can perform validation on the missing and forbidden template tags.
    """

    FORBIDDEN_TAGS: ClassVar[frozenset[str]] = frozenset({"autoescape"})

    def __init__(
        self,
        required_template_tags: Collection[str] = (),
        backend: str = "openforms.template.sandbox_backend",
    ):
        self.required_template_tags = required_template_tags
        self.backend = backend

    def _iter_tag_names(self, value: str) -> Iterator[str]:
        for token in Lexer(value).tokenize():
            # tags are BLOCK type tokens
            if token.token_type != TokenType.BLOCK:
                continue

            parts = token.contents.split()
            if parts:
                yield parts[0]

    def check_syntax_errors(self, value: str) -> None:
        backend = import_string(self.backend)
        try:
            parse(value, backend=backend)
        except TemplateSyntaxError as exc:
            raise ValidationError(str(exc), code="syntax_error") from exc

    def __call__(self, value: str) -> None:
        self.check_syntax_errors(value)

        forbidden_tags: set[str] = set()
        seen_tags: set[str] = set()
        missing_tags: set[str] = set()

        for name in self._iter_tag_names(value):
            if name in self.FORBIDDEN_TAGS:
                forbidden_tags.add(name)
            seen_tags.add(name)

        missing_tags = set(self.required_template_tags) - seen_tags

        errors = []

        if forbidden_tags:
            errors.append(
                ValidationError(
                    _("Forbidden template-tag found: {tag}").format(
                        tag=", ".join(
                            f"{{% {tag} %}}" for tag in sorted(forbidden_tags)
                        )
                    ),
                    code="invalid",
                )
            )

        if missing_tags:
            errors.append(
                ValidationError(
                    _("Missing required template-tag {tag}").format(
                        tag=", ".join(f"{{% {tag} %}}" for tag in sorted(missing_tags))
                    ),
                    code="invalid",
                )
            )

        if errors:
            raise ValidationError(errors)
