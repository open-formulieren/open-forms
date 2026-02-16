from collections.abc import Iterable

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


class ListMixin[T](SerializerContextMixin):
    """
    Fetch and serialize a list of objects.

    Alternative to :class:`rest_framework.mixins.ListModelMixin` for non-database
    backed collections of objects.
    """

    serializer_class: type[serializers.Serializer]

    def get_serializer(self, *args, **kwargs):
        kwargs.setdefault("context", self.get_serializer_context())
        kwargs["many"] = True
        return self.serializer_class(*args, **kwargs)

    def get_objects(self) -> Iterable[T]:
        raise NotImplementedError("You must implement the 'get_objects' method")

    def get(self, request, *args, **kwargs):
        objects = self.get_objects()
        serializer = self.get_serializer(instance=objects)
        return Response(serializer.data)
