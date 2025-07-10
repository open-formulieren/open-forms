import inspect
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.cache import SessionStore
from django.core.checks import Warning, register
from django.db import ProgrammingError

import structlog
from psycopg.errors import DatabaseError
from rest_framework.serializers import CharField, Serializer, empty
from rest_framework.test import APIRequestFactory

logger = structlog.stdlib.get_logger(__name__)


def get_subclasses(cls):
    for subclass in cls.__subclasses__():
        yield from get_subclasses(subclass)
        yield subclass


def is_subpath(*, parent: Path, child: str) -> bool:
    try:
        Path(child).relative_to(parent)
    except ValueError:
        return False
    return True


@register
def check_serializer_non_required_charfield_allow_blank_true(  # pragma: no cover
    app_configs, **kwargs
):
    """
    Check for serializers.CharFields that have ``required=False``, but not ``allow_blank=True``
    to avoid bogus validation errors occurring when empty strings are provided by the frontend.
    """
    request = APIRequestFactory().get("/")
    request.user = AnonymousUser()
    request.session = SessionStore()

    errors = []
    serializers = get_subclasses(Serializer)
    for serializer_class in serializers:
        serializer_defined_in = inspect.getfile(serializer_class)
        if not is_subpath(
            parent=settings.DJANGO_PROJECT_DIR, child=serializer_defined_in
        ):
            continue  # ignore code not defined in our own codebase

        if hasattr(serializer_class, "Meta") and not hasattr(
            serializer_class.Meta, "model"
        ):
            continue

        try:
            serializer = serializer_class(context={"request": request})
            fields = serializer.fields
        except (ProgrammingError, DatabaseError) as exc:
            logger.debug(
                "serializer_instantation_failure",
                serializer=serializer_class,
                exc_info=exc,
            )
            continue

        for field_name, field in fields.items():
            if not isinstance(field, CharField) or field.read_only:
                continue

            if (
                not field.required
                and field.default in ("", None, empty)
                and not field.allow_blank
            ):
                file_path = inspect.getfile(serializer_class)

                errors.append(
                    Warning(
                        (
                            f"{serializer_class.__module__}.{serializer_class.__qualname__}.{field_name} does not have `allow_blank=True`\n"
                            f"{file_path}"
                        ),
                        hint="Consider setting `allow_blank=True` to allow providing empty string values",
                        id="utils.W002",
                    )
                )
    return errors
