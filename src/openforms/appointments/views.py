import logging

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView

from drf_spectacular.utils import OpenApiResponse, extend_schema

from openforms.api.serializers import ExceptionSerializer
from openforms.config.models import GlobalConfiguration
from openforms.submissions.models import Submission
from openforms.submissions.utils import add_submmission_to_session

from .tokens import submission_appointment_token_generator

logger = logging.getLogger(__name__)


@extend_schema(
    summary=_("Verify the appointment cancel link."),
    responses={
        302: None,
        403: OpenApiResponse(
            response=ExceptionSerializer,
            description=_("Unable to verify token."),
        ),
    },
)
class VerifyCancelAppointmentLinkView(RedirectView):

    permission_classes = ()
    authentication_classes = ()

    def get_redirect_url(self, submission_uuid: int, token: str, *args, **kwargs):
        try:
            submission = Submission.objects.get(uuid=submission_uuid)
        except ObjectDoesNotExist:
            logger.debug(
                "Called endpoint with an invalid submission uuid: %s", submission_uuid
            )
            raise PermissionDenied("Cancel url is not valid")

        # Check that the token is valid
        valid = submission_appointment_token_generator.check_token(submission, token)
        if not valid:
            logger.debug("Called endpoint with an invalid token: %s", token)
            raise PermissionDenied("Cancel url is not valid")

        add_submmission_to_session(submission, self.request.session)

        config = GlobalConfiguration.get_solo()

        return (
            f"{config.cancel_appointment_page}"
            f"?time={submission.appointment_info.start_time.isoformat()}"
            f"&submission_uuid={str(submission_uuid)}"
        )
