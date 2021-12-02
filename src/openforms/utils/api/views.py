from rest_framework.response import Response


class ListMixin:
    """
    Fetch and serialize a list of objects.

    Alternative to :class:`rest_framework.mixins.ListModelMixin` for non-database
    backed collections of objects.
    """

    def get_serializer(self, **kwargs):
        return self.serializer_class(
            many=True,
            context={"request": self.request, "view": self},
            **kwargs,
        )

    def get(self, request, *args, **kwargs):
        objects = self.get_objects()
        serializer = self.get_serializer(instance=objects)
        return Response(serializer.data)
