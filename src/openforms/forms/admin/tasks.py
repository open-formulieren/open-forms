import os
import tempfile
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

from django.conf import settings
from django.core.files import File
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from openforms.celery import app
from openforms.utils.urls import build_absolute_uri

from ..models import Form
from ..models.form import FormsExport
from ..utils import export_form
from .tokens import exported_forms_token_generator


@app.task
def process_forms_export(forms_uuids, email, username):
    forms = Form.objects.filter(uuid__in=forms_uuids)

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
                zipfile.write(output_file, arcname=os.path.basename(output_file))

        with open(zip_filepath, "rb") as zipfile:
            forms_export = FormsExport.objects.create(
                export_content=File(zipfile, name=os.path.basename(zip_filepath)),
                user_email=email,
                username=username,
            )

        token = exported_forms_token_generator.make_token(forms_export)
        url = build_absolute_uri(
            reverse(
                "admin:download_forms_export",
                kwargs={"pk": forms_export.pk, "token": token},
            )
        )

        email_content = render_to_string(
            "admin/forms/formsexport/email_content.html", context={"download_url": url}
        )

        send_mail(
            subject=_("Forms export ready"),
            message=email_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
