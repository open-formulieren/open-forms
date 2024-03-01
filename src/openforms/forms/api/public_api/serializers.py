from rest_framework import serializers

from ...models import Form


class FormSerializer(serializers.ModelSerializer):

    class Meta:
        model = Form
        fields = (
            "uuid",
            "name",
            "internal_name",
            "slug",
        )
        ref_name = "PublicForm"
