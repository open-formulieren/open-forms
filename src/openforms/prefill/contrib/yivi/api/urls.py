from django.urls import path

from .views import AttributeGroupListView

app_name = "prefill_yivi"

urlpatterns = [
    path(
        "attribute-groups",
        AttributeGroupListView.as_view(),
        name="yivi-prefill-attributes-list",
    ),
]
