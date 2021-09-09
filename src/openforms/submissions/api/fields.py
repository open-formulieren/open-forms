from functools import reduce

from rest_framework_nested.relations import NestedHyperlinkedRelatedField


class NestedRelatedField(NestedHyperlinkedRelatedField):
    """
    Support lookups for lookup_field separated by __.
    """

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        underscored_obj_lookups = self.lookup_field.split("__")
        obj_for_lookup = reduce(getattr, [obj] + underscored_obj_lookups[:-1])

        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj_for_lookup, "pk") and obj_for_lookup.pk in (None, ""):
            return None

        # default lookup from rest_framework.relations.HyperlinkedRelatedField
        lookup_value = getattr(obj_for_lookup, underscored_obj_lookups[-1])
        kwargs = {self.lookup_url_kwarg: lookup_value}

        # multi-level lookup
        for parent_lookup_kwarg in list(self.parent_lookup_kwargs.keys()):
            underscored_lookup = self.parent_lookup_kwargs[parent_lookup_kwarg]

            # split each lookup by their __, e.g. "parent__pk" will be split into "parent" and "pk", or
            # "parent__super__pk" would be split into "parent", "super" and "pk"
            lookups = underscored_lookup.split("__")

            # use the Django ORM to lookup this value, e.g., obj.parent.pk
            lookup_value = reduce(getattr, [obj] + lookups)

            # store the lookup_name and value in kwargs, which is later passed to the reverse method
            kwargs.update({parent_lookup_kwarg: lookup_value})

        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class NestedSubmissionRelatedField(NestedHyperlinkedRelatedField):
    """
    Build nested related URLs for objects that are not directly related in the DB.

    This field relies on the serializer instance to fill out some url kwargs.
    """

    instance_lookup_kwargs = {}

    def __init__(self, *args, **kwargs):
        self.instance_lookup_kwargs = kwargs.pop(
            "instance_lookup_kwargs", self.instance_lookup_kwargs
        )
        kwargs["read_only"] = True
        super().__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        underscored_obj_lookups = self.lookup_field.split("__")
        obj_for_lookup = reduce(getattr, [obj] + underscored_obj_lookups[:-1])

        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj_for_lookup, "pk") and obj_for_lookup.pk in (None, ""):
            return None

        # default lookup from rest_framework.relations.HyperlinkedRelatedField
        lookup_value = getattr(obj_for_lookup, underscored_obj_lookups[-1])
        kwargs = {self.lookup_url_kwarg: lookup_value}

        # FIXME: this can probably be done in a cleaner way
        instance = self.parent.instance or obj

        # multi-level lookup
        for instance_lookup_kwarg in list(self.instance_lookup_kwargs.keys()):
            underscored_lookup = self.instance_lookup_kwargs[instance_lookup_kwarg]

            # split each lookup by their __, e.g. "instance__pk" will be split into "instance" and "pk", or
            # "instance__super__pk" would be split into "instance", "super" and "pk"
            lookups = underscored_lookup.split("__")

            # use the Django ORM to lookup this value, e.g., obj.instance.pk
            lookup_value = reduce(getattr, [instance] + lookups)

            # store the lookup_name and value in kwargs, which is later passed to the reverse method
            kwargs.update({instance_lookup_kwarg: lookup_value})

        return self.reverse(view_name, kwargs=kwargs, request=request, format=format)


class URLRelatedField(NestedHyperlinkedRelatedField):
    """This field still checks that the URL refers to a valid model in the database, but does not
    convert the URL to an actual object."""

    def to_internal_value(self, data):
        super().to_internal_value(data)
        return data

    def get_url(self, obj, view_name, request, format):
        return obj
