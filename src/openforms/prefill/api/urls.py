from django.urls import path

from .views import (
    PluginAttributesListView,
    PluginListView,
    PluginObjectsAPIAttributesListView,
    PluginObjectsAPIObjecttypeListView,
    PluginObjectsAPIObjecttypeVersionListView,
)

urlpatterns = [
    path(
        # "plugins/objects-api/objecttypes/<str:objects_api_group>",
        "plugins/objects-api/objecttypes",
        PluginObjectsAPIObjecttypeListView.as_view(),
        name="prefill-objects-api-objecttype-list",
    ),
    path(
        "plugins/objects-api/objecttypes/<uuid:objects_api_objecttype_uuid>/versions",
        PluginObjectsAPIObjecttypeVersionListView.as_view(),
        name="prefill-objects-api-objecttype-version-list",
    ),
    path(
        "plugins/objects-api/objecttypes/<uuid:objects_api_objecttype_uuid>/versions/<int:objects_api_objecttype_version>/attributes",
        PluginObjectsAPIAttributesListView.as_view(),
        name="prefill-objects-api-objecttype-attribute-list",
    ),
    path("plugins", PluginListView.as_view(), name="prefill-plugin-list"),
    path(
        "plugins/<slug:plugin>/attributes",
        PluginAttributesListView.as_view(),
        name="prefill-attribute-list",
    ),
]
