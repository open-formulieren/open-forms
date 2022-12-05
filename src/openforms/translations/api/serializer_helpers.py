from django.conf import settings

from glom import assign, glom
from rest_framework import serializers
from rest_framework.fields import empty

SerializerCls = type[serializers.ModelSerializer]


class TranslationsFieldMixin:
    def to_representation(self, instance):
        """
        Normalize None values to empty strings.

        We exclusively deal with translatable (thus string-based) fields.
        """
        ret = super().to_representation(instance)
        _readable_fields = [field.field_name for field in self._readable_fields]
        for key in list(ret.keys()):
            # only keep the fields that are readable
            if key not in _readable_fields:
                del ret[key]
            # normalize to strings
            elif ret[key] is None:
                ret[key] = ""
        return ret

    def run_validation(self, data=empty):
        result = super().run_validation(data=data)

        # map back to the correct source attributes so the values can be assigned
        # to the model fields
        rewritten_values = {}
        for field in self._writable_fields:
            value = result[field.field_name]
            lookup = ".".join(field.source_attrs)
            assign(rewritten_values, lookup, value, missing=dict)
        return rewritten_values

    def to_internal_value(self, data):
        values = super().to_internal_value(data)
        # undo the mapping to the source_attr so that the parent serializer validation
        # can correctly validate the language agnostic fields. We map them back for
        # final processing in run_validation.
        rewritten_values = {}
        for field in self._writable_fields:
            lookup = ".".join(field.source_attrs)
            value = glom(values, lookup, default="")
            rewritten_values[field.field_name] = value
        return rewritten_values


def build_translated_model_fields_serializer(
    base: SerializerCls,
    language_code: str,
    fields: list[str],
) -> SerializerCls:
    """
    Build a derived serializer class with a unique name for drf-spectacular.
    """
    # build a model serializer with the same validation rules as the parent, but
    # only for the translatable fields, meaning we skip the base._declared_fields.
    if set(base._declared_fields).intersection(set(fields)):
        raise TypeError("Declared translatable fields are currently not supported.")

    model_fields = {
        f.name: f for f in base.Meta.model._meta.get_fields() if f.name in fields
    }

    # create the Meta class, which inherits from the base Meta
    Meta = type(
        "Meta",
        (base.Meta,),
        {
            "fields": fields,
            # Specify the serializer <-> model field lookups via extra_kwargs.
            # Note that this does *not yet* take into account any possible
            # superclass extra_kwargs defined (such as validators).
            "extra_kwargs": {
                field: {
                    "source": f"{field}_{language_code}",
                    "allow_blank": language_code != settings.LANGUAGE_CODE
                    or model_fields[field].blank,
                }
                for field in fields
            },
        },
    )

    basename = base.__name__.replace("Serializer", "")
    suffix = f"{language_code.upper()}TranslationsSerializer"
    NestedModelSerializer = type(
        f"{basename}{suffix}",
        (TranslationsFieldMixin, base),
        {
            "Meta": Meta,
        },
    )
    return NestedModelSerializer
