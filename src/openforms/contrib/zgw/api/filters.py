from rest_framework import serializers

from ..clients import CatalogiClient


class ProvidesCatalogiClientQueryParamsSerializer(serializers.Serializer):

    def get_ztc_client(self) -> CatalogiClient:
        raise NotImplementedError()
