from rest_framework import serializers

from openforms.accounts.api.serializers import UserSerializer

from ...models import FormVersion


class FormVersionSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer(required=False, read_only=True)

    class Meta:
        model = FormVersion
        fields = (
            "uuid",
            "created",
            "user",
            "description",
        )
