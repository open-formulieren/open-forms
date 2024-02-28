from typing import TypedDict

from rest_framework import serializers

from openforms.forms.models import Category


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    ancestors = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Category
        fields = (
            "url",
            "name",
            "uuid",
            "ancestors",
            "depth",
        )
        extra_kwargs = {
            "url": {
                "view_name": "api:categories-detail",
                "lookup_field": "uuid",
            },
        }

    class NameUUID(TypedDict):
        name: str
        uuid: str

    def get_ancestors(self, obj) -> list[NameUUID]:
        ancestors = obj.get_ancestors()
        return [{"uuid": str(n.uuid), "name": n.name} for n in ancestors]
