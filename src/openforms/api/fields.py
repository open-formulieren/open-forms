import uuid
from collections.abc import Collection
from typing import ClassVar

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SkipField, empty

from openforms.utils.base64_image import decode_base64_image


class PrimaryKeyRelatedAsChoicesField(serializers.PrimaryKeyRelatedField):
    """
    Custom subclass to register a custom drf-jsonschema-serializer converter.
    """

    pass


class SlugRelatedAsChoicesField(serializers.SlugRelatedField):
    """
    Custom subclass to register a custom drf-jsonschema-serializer converter.
    """

    pass


class JSONFieldWithSchema(serializers.JSONField):
    """
    Custom subclass to register a custom drf-jsonschema-serializer converter.
    """

    @property
    def schema(self):
        return {
            "type": "object",
            "properties": {},
        }


class RelatedFieldFromContext(serializers.HyperlinkedRelatedField):
    """
    Look up the object in the serializer context.
    """

    def __init__(self, context_name="objects", *args, **kwargs):
        super().__init__(*args, **kwargs)
        # key to use to look up the object in the context, which is a dict mapping
        # of :arg`lookup_field` to the instance(s)
        self.context_name = context_name

    def get_object(self, view_name, view_args, view_kwargs):
        # these view_args and view_kwargs come from processing the input URL,
        # which lead to a valid resolver match.
        input_url = self.reverse(view_name, args=view_args, kwargs=view_kwargs)

        # grab the object from the context
        obj_collection = self.parent.context[self.context_name]
        lookup_value = view_kwargs[self.lookup_url_kwarg]
        try:
            obj = obj_collection[lookup_value]
        except KeyError:
            self.fail("does_not_exist")
        context_obj_url = self.get_url(obj, view_name, None, None)

        if input_url != context_obj_url:
            self.fail("incorrect_match")
        return obj


class Base64ImageField(serializers.ImageField):
    """
    Accept image data that's base64 encoded and store it in an ``ImageField``.

    The implementation is inspired by django-extra-fields which is unmaintained.
    """

    ALLOWED_EXTENSIONS: ClassVar[Collection[str]] = frozenset(
        (
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        )
    )

    def __init__(self, *args, **kwargs):
        kwargs["use_url"] = True  # output URL when serializing
        super().__init__(*args, **kwargs)

    def run_validation(self, data=empty):
        # do nothing
        if data == "" and self.allow_empty_file:
            raise SkipField()
        # clear the field if it can be empty and & we get an explicit 'null'
        if data is None and self.allow_empty_file:
            return ""
        if not data:
            self.fail("empty")
        return super().run_validation(data)

    def to_internal_value(self, data):
        # we must cast because the drf-stubs force `File` as type, which is wrong because
        # we use base64...
        from typing import cast  # noqa: TID251

        data = data or ""
        if not isinstance(data, str):  # pragma: no cover
            self.fail("invalid")

        assert data
        data = cast(str, data)  # pyright infers Literal[""] from the parent types...
        (content, extension, mime_type) = decode_base64_image(data)
        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(
                _("Invalid file type '{ext}'.").format(ext=extension),
                code="invalid",
            )

        file = SimpleUploadedFile(
            # generate a file name
            name=f"{uuid.uuid4()}{extension}",
            content=content,
            content_type=mime_type,
        )

        return super().to_internal_value(file)
