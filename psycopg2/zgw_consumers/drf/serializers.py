"""
Support "ModelSerializer" for dataclass based "models".

The :class:`APIModelSerializer` is able to introspect the class typehints to generate
the appropriate serializer fields.

Currently the support is experimental.
"""
import copy
from collections import OrderedDict
from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from rest_framework import fields, serializers

from .utils import extract_model_field_type, get_field_kwargs


class APIModelSerializer(serializers.Serializer):
    serializer_field_mapping = {
        str: fields.CharField,
        int: fields.IntegerField,
        float: fields.FloatField,
        Decimal: fields.DecimalField,
        date: fields.DateField,
        datetime: fields.DateTimeField,
        time: fields.TimeField,
        bool: fields.BooleanField,
        UUID: fields.UUIDField,
    }

    def get_fields(self):
        assert hasattr(
            self, "Meta"
        ), 'Class {serializer_class} missing "Meta" attribute'.format(
            serializer_class=self.__class__.__name__
        )
        assert hasattr(
            self.Meta, "model"
        ), 'Class {serializer_class} missing "Meta.model" attribute'.format(
            serializer_class=self.__class__.__name__
        )

        declared_fields = copy.deepcopy(self._declared_fields)
        model = self.Meta.model
        depth = getattr(self.Meta, "depth", 0)

        if depth is not None:
            assert depth >= 0, "'depth' may not be negative."
            assert depth <= 10, "'depth' may not be greater than 10."

        field_names = self.get_field_names(declared_fields)

        extra_kwargs = self.get_extra_kwargs()

        # Determine the fields that should be included on the serializer.
        fields = OrderedDict()

        for field_name in field_names:
            # If the field is explicitly declared on the class then use that.
            if field_name in declared_fields:
                fields[field_name] = declared_fields[field_name]
                continue

            extra_field_kwargs = extra_kwargs.get(field_name, {})
            source = extra_field_kwargs.get("source", "*")
            if source == "*":
                source = field_name

            # Determine the serializer field class and keyword arguments.
            field_class, field_kwargs = self.build_field(source, model)

            # Include any kwargs defined in `Meta.extra_kwargs`
            field_kwargs = self.include_extra_kwargs(field_kwargs, extra_field_kwargs)

            # Create the serializer field.
            fields[field_name] = field_class(**field_kwargs)

        return fields

    def get_field_names(self, declared_fields):
        fields = self.Meta.fields
        # Ensure that all declared fields have also been included in the
        # `Meta.fields` option.

        # Do not require any fields that are declared in a parent class,
        # in order to allow serializer subclasses to only include
        # a subset of fields.
        required_field_names = set(declared_fields)
        for cls in self.__class__.__bases__:
            required_field_names -= set(getattr(cls, "_declared_fields", []))

        for field_name in required_field_names:
            assert field_name in fields, (
                "The field '{field_name}' was declared on serializer "
                "{serializer_class}, but has not been included in the "
                "'fields' option.".format(
                    field_name=field_name, serializer_class=self.__class__.__name__
                )
            )
        return fields

    def get_extra_kwargs(self):
        """
        Return a dictionary mapping field names to a dictionary of
        additional keyword arguments.
        """
        extra_kwargs = copy.deepcopy(getattr(self.Meta, "extra_kwargs", {}))

        read_only_fields = getattr(self.Meta, "read_only_fields", None)
        if read_only_fields is not None:
            if not isinstance(read_only_fields, (list, tuple)):
                raise TypeError(
                    "The `read_only_fields` option must be a list or tuple. "
                    "Got %s." % type(read_only_fields).__name__
                )
            for field_name in read_only_fields:
                kwargs = extra_kwargs.get(field_name, {})
                kwargs["read_only"] = True
                extra_kwargs[field_name] = kwargs

        else:
            # Guard against the possible misspelling `readonly_fields` (used
            # by the Django admin and others).
            assert not hasattr(self.Meta, "readonly_fields"), (
                "Serializer `%s.%s` has field `readonly_fields`; "
                "the correct spelling for the option is `read_only_fields`."
                % (self.__class__.__module__, self.__class__.__name__)
            )

        return extra_kwargs

    def include_extra_kwargs(self, kwargs, extra_kwargs):
        """
        Include any 'extra_kwargs' that have been included for this field,
        possibly removing any incompatible existing keyword arguments.
        """
        if extra_kwargs.get("read_only", False):
            for attr in [
                "required",
                "default",
                "allow_blank",
                "allow_null",
                "min_length",
                "max_length",
                "min_value",
                "max_value",
                "validators",
                "queryset",
            ]:
                kwargs.pop(attr, None)

        if extra_kwargs.get("default") and kwargs.get("required") is False:
            kwargs.pop("required")

        if extra_kwargs.get("read_only", kwargs.get("read_only", False)):
            extra_kwargs.pop(
                "required", None
            )  # Read only fields should always omit the 'required' argument.

        kwargs.update(extra_kwargs)

        return kwargs

    def build_field(self, field_name, model_class):
        model_field_type = extract_model_field_type(model_class, field_name)
        return self.build_standard_field(field_name, model_field_type)

    def build_standard_field(self, field_name, model_field_type):
        """
        Create regular model fields.
        """
        field_mapping = self.serializer_field_mapping
        field_class = field_mapping[model_field_type]
        field_kwargs = get_field_kwargs(field_name, model_field_type)

        if "choices" in field_kwargs:
            # Fields with choices get coerced into `ChoiceField`
            # instead of using their regular typed field.
            field_class = self.serializer_choice_field
            # Some model fields may introduce kwargs that would not be valid
            # for the choice field. We need to strip these out.
            # Eg. models.DecimalField(max_digits=3, decimal_places=1, choices=DECIMAL_CHOICES)
            valid_kwargs = {
                "read_only",
                "write_only",
                "required",
                "default",
                "initial",
                "source",
                "label",
                "help_text",
                "style",
                "error_messages",
                "validators",
                "allow_null",
                "allow_blank",
                "choices",
            }
            for key in list(field_kwargs):
                if key not in valid_kwargs:
                    field_kwargs.pop(key)

        if not issubclass(field_class, fields.CharField) and not issubclass(
            field_class, fields.ChoiceField
        ):
            # `allow_blank` is only valid for textual fields.
            field_kwargs.pop("allow_blank", None)

        return field_class, field_kwargs
