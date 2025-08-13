from django.urls import path

from .views import AttributeGroupListView

app_name = "authentication_yivi"

urlpatterns = [
    path(
        "attribute-groups",
        AttributeGroupListView.as_view(),
        name="attribute-group-list",
    ),
]
