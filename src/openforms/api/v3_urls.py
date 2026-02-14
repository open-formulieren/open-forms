from django.urls import include, path

from rest_framework import routers

from openforms.forms.api.v3.viewsets import FormViewSet
from openforms.utils.decorators import never_cache
from openforms.utils.urls import decorator_include

router = routers.DefaultRouter(trailing_slash=False)
router.register(r"forms", FormViewSet, basename="form")

app_name = "api"


urlpatterns = [
    path(
        "v3/",
        decorator_include(
            never_cache,
            [
                path("", include(router.urls)),
            ],
        ),
    ),
]
