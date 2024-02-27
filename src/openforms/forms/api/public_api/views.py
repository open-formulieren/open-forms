from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import ListAPIView

from ...models import Form
from .filters import FormCategoryNameFilter
from .serializers import FormSerializer


class FormListView(ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAdminUser,)

    serializer_class = FormSerializer
    filterset_class = FormCategoryNameFilter
    queryset = Form.objects.filter(_is_deleted=False)

    # TODO - Remove when we add pagination
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.data = {"results": response.data}
        return response
