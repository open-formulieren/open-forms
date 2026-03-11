from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import structlog

from openforms.authentication.service import check_user_is_submission_initiator
from openforms.forms.models import Form
from openforms.utils.widgets import OpenFormsTextInput

from .models import CosignOTP, Submission

logger = structlog.stdlib.get_logger()


class SearchSubmissionForCosignForm(forms.Form):
    code = forms.CharField(
        label=_("Code"),
        help_text=_(
            "You should have received this code in the email requesting you to cosign a form."
        ),
        required=True,
        widget=OpenFormsTextInput(),
    )

    def __init__(self, instance: Form, *args, **kwargs):
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        self.form = instance

    def clean(self):
        submission = Submission.objects.filter(
            public_registration_reference=self.cleaned_data["code"],
            form=self.form,
        ).first()
        # always store the resolved submission so that form_invalid can handle it
        self.cleaned_data["submission"] = submission

        # check that we actually expect cosign for this submission
        if not submission or not submission.cosign_state.is_waiting:
            self.add_error(
                "code",
                _(
                    "Could not find a submission corresponding to this code that requires "
                    "co-signing"
                ),
            )
        elif check_user_is_submission_initiator(self.request, submission):
            logger.info(
                "cosign_start_blocked",
                reason="cosigner_same_as_submitter",
                submission_uuid=str(submission.uuid),
            )
            self.add_error(
                "code",
                _("The submission cannot be co-signed by the original submitter."),
            )

        return self.cleaned_data


class CosignOTPForm(forms.Form):
    otp = forms.CharField(
        label=_("One-time password"),
        help_text=_(
            "The one-time password was sent to the same email address where you "
            "received the cosign request."
        ),
        required=True,
        max_length=10,  # allow for some spaces/dashes from bad copy-pasting
        widget=OpenFormsTextInput(),
    )

    def __init__(self, instance: Submission, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.submission = instance

    def clean_otp(self):
        # only consider the digits in the code
        cleaned_code = "".join(
            char for char in self.cleaned_data["otp"] if char.isdigit()
        )
        valid_otp = CosignOTP.objects.filter(
            submission=self.submission,
            verification_code=cleaned_code,
            expires_at__gt=timezone.now(),
        ).first()
        if valid_otp is None:
            raise forms.ValidationError(
                _("The code you entered is invalid or has expired.")
            )
        assert not valid_otp.is_expired
        return cleaned_code
