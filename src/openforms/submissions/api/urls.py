from rest_framework import routers

from openforms.core.api.viewsets import (
    SubmissionViewSet
)


router = routers.SimpleRouter()
router.register(r'^', FormSubmissionViewSet)

urlpatterns = router.urls