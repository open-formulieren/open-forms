from django.views.generic import DetailView

from openforms.submissions.models import Submission
from openforms.utils.views import DevViewMixin, EmailDebugViewMixin

from .plugin import EmailRegistration


class EmailRegistrationTestView(DevViewMixin, EmailDebugViewMixin, DetailView):
    model = Submission
    pk_url_kwarg = "submission_id"

    def get_email_content(self):
        mode = self._get_mode()
        (
            subject,
            html_content,
            text_content,
        ) = EmailRegistration.render_registration_email(  # pyright: ignore[reportAttributeAccessIssue]
            self.object, is_payment_update=False
        )
        content = html_content if mode == "html" else text_content
        return content
