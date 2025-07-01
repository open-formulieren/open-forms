from __future__ import annotations

from collections.abc import Sequence
from pathlib import PurePosixPath

from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from openforms.config.data import Action
from openforms.contrib.microsoft.client import (
    MSGraphClient,
    MSGraphUploadHelper,
)
from openforms.contrib.microsoft.exceptions import MSAuthenticationError
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.registrations.contrib.microsoft_graph.models import (
    MSGraphRegistrationConfig,
)
from openforms.submissions.models import Submission, SubmissionReport
from openforms.template import render_from_string

from ...base import BasePlugin
from ...exceptions import RegistrationFailed
from ...registry import register
from .config import MicrosoftGraphOptions, MicrosoftGraphOptionsSerializer


@register("microsoft-graph")
class MSGraphRegistration(BasePlugin[MicrosoftGraphOptions]):
    verbose_name = _("Microsoft Graph (OneDrive/SharePoint)")
    configuration_options = MicrosoftGraphOptionsSerializer

    @staticmethod
    def _get_folder_name(
        submission: Submission, options: MicrosoftGraphOptions
    ) -> PurePosixPath:
        now_utc = timezone.now()
        date = timezone.localtime(now_utc).date()
        folder_path = render_from_string(
            options["folder_path"],
            {
                "year": f"{date:%Y}",
                "month": f"{date:%m}",
                "day": f"{date:%d}",
            },
        )

        return PurePosixPath(
            folder_path,
            slugify(submission.form.admin_name),
            submission.public_registration_reference,
        )

    def register_submission(
        self, submission: Submission, options: MicrosoftGraphOptions
    ) -> None:
        config = MSGraphRegistrationConfig.get_solo()
        if not config.service:
            raise RegistrationFailed("No service configured.")

        client = MSGraphClient(config.service)
        uploader = MSGraphUploadHelper(client, options)

        folder_name = self._get_folder_name(submission, options)

        submission_report = SubmissionReport.objects.get(submission=submission)
        uploader.upload_django_file(
            submission_report.content, folder_name / "report.pdf"
        )

        data = submission.data
        data["__metadata__"] = {"submission_language": submission.language_code}
        uploader.upload_json(data.data, folder_name / "data.json")

        for attachment in submission.attachments.order_by("pk"):
            uploader.upload_django_file(
                attachment.content,
                folder_name / "attachments" / attachment.get_display_name(),
            )

        self._set_payment(uploader, submission, folder_name)

    def update_payment_status(
        self, submission: Submission, options: MicrosoftGraphOptions
    ):
        config = MSGraphRegistrationConfig.get_solo()
        client = MSGraphClient(config.service)
        uploader = MSGraphUploadHelper(client, options)

        folder_name = self._get_folder_name(submission, options)
        self._set_payment(uploader, submission, folder_name)

    def _set_payment(self, uploader, submission, folder_name):
        if submission.payment_required:
            if submission.payment_user_has_paid:
                content = f"{_('payment received')}: € {submission.price}"
            else:
                content = f"{_('payment required')}: € {submission.price}"
            uploader.upload_string(content, folder_name / "payment_status.txt")

    def check_config(self):
        config = MSGraphRegistrationConfig.get_solo()
        if not config.service_id:
            raise InvalidPluginConfiguration(_("MSGraphService not selected"))

        # check connection
        try:
            client = MSGraphClient(config.service, force_auth=True)
        except MSAuthenticationError as e:
            raise InvalidPluginConfiguration(
                _("Could not connect: {exception}").format(exception=e)
            )
        else:
            try:
                storage = client.account.storage()
                drive = storage.get_default_drive()
                assert drive is not None
                drive.get_root_folder()
            except Exception as e:
                raise InvalidPluginConfiguration(
                    _("Could not access root folder: {exception}").format(exception=e)
                )

    def get_config_actions(self) -> Sequence[Action]:
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:registrations_microsoft_graph_msgraphregistrationconfig_change",
                    args=(MSGraphRegistrationConfig.singleton_instance_id,),
                ),
            ),
        ]
