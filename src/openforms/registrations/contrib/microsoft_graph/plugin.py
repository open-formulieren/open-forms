from typing import NoReturn

from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from openforms.contrib.microsoft.client import MSGraphClient, MSGraphUploadHelper
from openforms.contrib.microsoft.exceptions import MSAuthenticationError
from openforms.plugins.exceptions import InvalidPluginConfiguration, PluginNotEnabled
from openforms.registrations.contrib.microsoft_graph.models import (
    MSGraphRegistrationConfig,
)
from openforms.submissions.models import Submission, SubmissionReport
from openforms.submissions.tasks.registration import set_submission_reference

from ...base import BasePlugin
from ...exceptions import NoSubmissionReference, RegistrationFailed
from ...registry import register


@register("microsoft-graph")
class MSGraphRegistration(BasePlugin):
    verbose_name = _("Microsoft Graph (OneDrive/SharePoint)")

    def _get_folder_name(self, submission: Submission):
        return f"open-forms/{slugify(submission.form.admin_name)}/{submission.public_registration_reference}"

    def register_submission(self, submission: Submission, options: dict) -> None:
        if not self.is_enabled:
            raise PluginNotEnabled()

        # explicitly get a reference before registering
        set_submission_reference(submission)

        config = MSGraphRegistrationConfig.get_solo()
        if not config.service:
            raise RegistrationFailed("No service configured.")

        client = MSGraphClient(config.service)
        uploader = MSGraphUploadHelper(client)

        folder_name = self._get_folder_name(submission)

        submission_report = SubmissionReport.objects.get(submission=submission)
        uploader.upload_django_file(
            submission_report.content, f"{folder_name}/report.pdf"
        )

        data = submission.get_merged_data()
        uploader.upload_json(data, f"{folder_name}/data.json")

        for attachment in submission.attachments.all():
            uploader.upload_django_file(
                attachment.content, f"{folder_name}/attachments/{attachment.file_name}"
            )

        self._set_payment(uploader, submission, folder_name)

    def get_reference_from_result(self, result: None) -> NoReturn:
        raise NoSubmissionReference("MS Graph plugin does not emit a reference")

    def update_payment_status(self, submission: "Submission", options: dict):
        config = MSGraphRegistrationConfig.get_solo()
        client = MSGraphClient(config.service)
        uploader = MSGraphUploadHelper(client)

        folder_name = self._get_folder_name(submission)
        self._set_payment(uploader, submission, folder_name)

    def _set_payment(self, uploader, submission, folder_name):
        if submission.payment_required:
            if submission.payment_user_has_paid:
                content = f"{_('payment received')}: € {submission.price}"
            else:
                content = f"{_('payment required')}: € {submission.price}"
            uploader.upload_string(content, f"{folder_name}/payment_status.txt")

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
                drive.get_root_folder()
            except Exception as e:
                raise InvalidPluginConfiguration(
                    _("Could not access root folder: {exception}").format(exception=e)
                )

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:registrations_microsoft_graph_msgraphregistrationconfig_change",
                    args=(MSGraphRegistrationConfig.singleton_instance_id,),
                ),
            ),
        ]
