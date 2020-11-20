from functools import reduce

from rest_framework_nested.relations import NestedHyperlinkedRelatedField


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
        super().__init__(*args, **kwargs)

    def get_url(self, obj, view_name, request, format):
        """
        Given an object, return the URL that hyperlinks to the object.

        May raise a `NoReverseMatch` if the `view_name` and `lookup_field`
        attributes are not configured to correctly match the URL conf.
        """
        # Unsaved objects will not yet have a valid URL.
        if hasattr(obj, "pk") and obj.pk in (None, ""):
            return None

        # default lookup from rest_framework.relations.HyperlinkedRelatedField
        lookup_value = getattr(obj, self.lookup_field)
        kwargs = {self.lookup_url_kwarg: lookup_value}

        instance = self.parent.instance

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
