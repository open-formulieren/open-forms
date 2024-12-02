from django.urls import path

from .views import (
    CaseTypesListView,
    CatalogueListView,
    DocumentTypesListView,
    ProductsListView,
    RoleTypeListView,
)

app_name = "zgw_apis"

urlpatterns = [
    path("catalogues", CatalogueListView.as_view(), name="catalogue-list"),
    path("case-types", CaseTypesListView.as_view(), name="case-type-list"),
    path("document-types", DocumentTypesListView.as_view(), name="document-type-list"),
    path("role-types", RoleTypeListView.as_view(), name="role-type-list"),
    path("products", ProductsListView.as_view(), name="product-list"),
]
