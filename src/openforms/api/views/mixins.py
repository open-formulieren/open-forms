from collections.abc import Callable, Iterable
from typing import Any

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response


class SerializerContextMixin:
    request: Request
    format_kwarg: str

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        return {"request": self.request, "format": self.format_kwarg, "view": self}


class ListMixin(SerializerContextMixin):
    """
    Fetch and serialize a list of objects.

    Alternative to :class:`rest_framework.mixins.ListModelMixin` for non-database
    backed collections of objects.
    """

    serializer_class: type[serializers.Serializer]
    get_objects: Callable[[], Iterable[Any]]

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", self.get_serializer_context())
        return self.serializer_class(many=True, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        objects = self.get_objects()
        serializer = self.get_serializer(instance=objects)

        return Response(serializer.data)
