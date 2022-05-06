from rest_framework import serializers


class ButtonTextSerializer(serializers.Serializer):
    resolved = serializers.SerializerMethodField()
    value = serializers.CharField(allow_blank=True)

    def __init__(self, resolved_getter=None, raw_field=None, *args, **kwargs):
        kwargs.setdefault("source", "*")
        self.resolved_getter = resolved_getter
        self.raw_field = raw_field
        super().__init__(*args, **kwargs)

    def bind(self, field_name, parent):
        super().bind(field_name, parent)

        if self.resolved_getter is None:
            self.resolved_getter = f"get_{field_name}"

        if self.raw_field is None:
            self.raw_field = field_name

        value_field = self.fields["value"]
        value_field.source = self.raw_field
        value_field.bind(value_field.field_name, self)

    def get_resolved(self, obj) -> str:
        return getattr(obj, self.resolved_getter)()
