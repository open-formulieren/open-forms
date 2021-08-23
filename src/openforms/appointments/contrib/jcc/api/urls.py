from django.urls import path

from .views import ProductsListView

urlpatterns = [
    path("products", ProductsListView.as_view(), name="jcc-products-list"),
]
