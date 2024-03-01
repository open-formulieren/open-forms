from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from ...models import Category
from ..permissions import FormAPIPermissions
from ..serializers.category import CategorySerializer
from .permissions import ViewCategoryPermission


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # TODO this permission isn't ideal with its mix of public and write access
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = [ViewCategoryPermission | FormAPIPermissions]
    pagination_class = None
    lookup_field = "uuid"
