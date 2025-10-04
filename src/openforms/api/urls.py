from django.urls import include, path
from django.views.generic import RedirectView

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularJSONAPIView,
    SpectacularRedocView,
)
from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter

from openforms.config.api.viewsets import ThemeViewSet
from openforms.contrib.reference_lists.api.views import (
    ReferenceListsTableItemsViewSet,
    ReferenceListsTablesViewSet,
)
from openforms.forms.api.public_api.viewsets import CategoryViewSet
from openforms.forms.api.viewsets import (
    FormDefinitionViewSet,
    FormsImportAPIView,
    FormStepViewSet,
    FormVersionViewSet,
    FormViewSet,
)
from openforms.products.api.viewsets import ProductViewSet
from openforms.services.api.viewsets import ServiceViewSet
from openforms.submissions.api.viewsets import SubmissionStepViewSet, SubmissionViewSet
from openforms.utils.decorators import never_cache
from openforms.utils.json_logic.api.views import GenerateLogicDescriptionView
from openforms.utils.urls import decorator_include
from openforms.variables.api.viewsets import ServiceFetchConfigurationViewSet

from .views import PingView

# from .schema import schema_view

app_name = "api"

router = routers.DefaultRouter(trailing_slash=False)
# form definitions, raw Formio output
router.register(r"form-definitions", FormDefinitionViewSet)

# forms & their steps
router.register(r"forms", FormViewSet)
forms_router = NestedSimpleRouter(router, r"forms", lookup="form")
forms_router.register(r"steps", FormStepViewSet, basename="form-steps")
forms_router.register(r"versions", FormVersionViewSet, basename="form-versions")

# form decoration
# Expose this endpoint on 2 different URLs
router.register(r"categories", CategoryViewSet, basename="legacy-categories")
router.register(r"public/categories", CategoryViewSet, basename="categories")

# submissions API
router.register(r"submissions", SubmissionViewSet)
submissions_router = NestedSimpleRouter(router, r"submissions", lookup="submission")
submissions_router.register(
    r"steps", SubmissionStepViewSet, basename="submission-steps"
)

# products
router.register("products", ProductViewSet)

# services
router.register("services", ServiceViewSet)

# service fetch configurations
router.register("service-fetch-configurations", ServiceFetchConfigurationViewSet)

# configuration
router.register("themes", ThemeViewSet, basename="themes")

urlpatterns = [
    path("docs/", RedirectView.as_view(pattern_name="api:api-docs")),
    # API documentation
    path(
        "v2/",
        include(
            [
                path(
                    "",
                    SpectacularJSONAPIView.as_view(schema=None),
                    name="api-schema-json",
                ),
                path(
                    "docs/",
                    SpectacularRedocView.as_view(url_name="api:api-schema-json"),
                    name="api-docs",
                ),
                path("schema", SpectacularAPIView.as_view(schema=None), name="schema"),
            ]
        ),
    ),
    # actual API endpoints
    path(
        "v2/",
        decorator_include(
            never_cache,
            [
                path("ping", PingView.as_view(), name="ping"),
                path("submissions/", include("openforms.submissions.api.urls")),
                path("analytics/", include("openforms.analytics_tools.api.urls")),
                path("forms-import", FormsImportAPIView.as_view(), name="forms-import"),
                path("prefill/", include("openforms.prefill.api.urls")),
                path("validation/", include("openforms.validations.api.urls")),
                path(
                    "logic/description",
                    GenerateLogicDescriptionView.as_view(),
                    name="generate-logic-description",
                ),
                path("authentication/", include("openforms.authentication.api.urls")),
                path("registration/", include("openforms.registrations.api.urls")),
                path("objects-api/", include("openforms.contrib.objects_api.api.urls")),
                path("payment/", include("openforms.payments.api.urls")),
                path("dmn/", include("openforms.dmn.api.urls")),
                path("translations/", include("openforms.translations.urls")),
                path("variables/", include("openforms.variables.urls")),
                path("public/", include("openforms.api.public_urls")),
                path(
                    "appointments/",
                    include("openforms.appointments.api.urls"),
                ),
                path("formio/", include("openforms.formio.api.urls")),
                path("geo/", include("openforms.contrib.kadaster.api.urls")),
                path("i18n/", include("openforms.translations.api.urls")),
                path(
                    "reference-lists-tables/<slug:service_slug>",
                    ReferenceListsTablesViewSet.as_view(),
                    name="reference-lists-tables-list",
                ),
                path(
                    "reference-lists-tables/<slug:service_slug>/<str:table_code>/table-items",
                    ReferenceListsTableItemsViewSet.as_view(),
                    name="reference-lists-table-items-list",
                ),
                path("", include(router.urls)),
                path("", include(forms_router.urls)),
                path("", include(submissions_router.urls)),
            ],
        ),
    ),
]
