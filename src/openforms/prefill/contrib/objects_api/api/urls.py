from django.urls import path

from .views import ObjecttypePropertiesListView

app_name = "prefill_objects_api"

urlpatterns = [
    path(
        "objecttypes/<uuid:objecttype_uuid>/versions/<int:objecttype_version>/properties",
        ObjecttypePropertiesListView.as_view(),
        name="objecttype-property-list",
    ),
]
