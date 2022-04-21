import logging
import tempfile
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from django.conf import settings
from django.core.files import File
from django.core.management import call_command
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from openforms.accounts.models import User
from openforms.celery import app
from openforms.emails.utils import send_mail_html
from openforms.utils.urls import build_absolute_uri

from ..models import Form
from ..models.form import FormsExport
from ..utils import export_form

logger = logging.getLogger(__name__)


@app.task
def process_forms_export(forms_uuids: list, user_id: int) -> None:
    forms = Form.objects.filter(uuid__in=forms_uuids)

    user = User.objects.get(id=user_id)

    # This deletes the temp dir once the context manager is exited
    with tempfile.TemporaryDirectory(dir=settings.PRIVATE_MEDIA_ROOT) as temp_dir:
        output_files = []
        for form in forms:
            output_files.append(
                export_form(
                    form_id=form.pk,
                    archive_name=Path(temp_dir, f"form_{form.uuid}.zip"),
                )
            )

        zip_filepath = Path(temp_dir, f"forms-export_{uuid4()}.zip")
        with ZipFile(zip_filepath, "w") as zipfile:
            for output_file in output_files:
                zipfile.write(output_file, arcname=Path(output_file).name)

        with open(zip_filepath, "rb") as zipfile:
            forms_export = FormsExport.objects.create(
                export_content=File(zipfile, name=Path(zip_filepath).name),
                user=user,
            )

        url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"uuid": forms_export.uuid},
            )
        )

        email_content = render_to_string(
            "admin/forms/formsexport/email_content.html", context={"download_url": url}
        )

        send_mail_html(
            subject=_("Forms export ready"),
            html_body=email_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )


@app.task
def clear_forms_export():
    logger.debug("Clearing old export files")
    call_command("delete_export_files")
