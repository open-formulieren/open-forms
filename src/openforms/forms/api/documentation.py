from rest_framework.serializers import Serializer


def get_admin_fields_markdown(serializer_class: Serializer, subpath=None):
    return "\n".join(
        [
            f"- `{subpath}.{field}`" if subpath else f"- `{field}`"
            for field in serializer_class._get_admin_field_names()
        ]
    )
