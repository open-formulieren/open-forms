from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class NoPagination(BasePagination):
    def paginate_queryset(self, queryset, request, view=None):
        return queryset

    def get_paginated_response(self, data):
        return Response({"results": data})

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "results": schema,
            },
        }
