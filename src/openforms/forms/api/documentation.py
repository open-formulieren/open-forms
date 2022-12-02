from openforms.api.serializers import PublicFieldsSerializerMixin


def get_admin_fields_markdown(serializer_class: type[PublicFieldsSerializerMixin]):
    return "\n".join(
        [f"- `{field}`" for field in serializer_class._get_admin_field_names()]
    )
