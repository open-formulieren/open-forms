from rest_framework import serializers


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
