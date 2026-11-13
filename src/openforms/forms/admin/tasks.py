import tempfile
import zipfile
from collections.abc import Collection
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files import File
from django.core.files.storage import storages
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from rest_framework.exceptions import ValidationError

from openforms.accounts.models import User
from openforms.celery import app
from openforms.config.models import Theme
from openforms.emails.utils import send_mail_html
from openforms.logging import audit_logger
from openforms.utils.urls import build_absolute_uri

from ..import_export.constants import FormConfigurationOptions
from ..import_export.service import (
    FormExportOptions,
    FormExportOptionsData,
    FormImportOptions,
    FormImportOptionsData,
    export_multiple_forms,
    import_form,
)
from ..models import Category
from ..models.form import FormsExport

logger = structlog.stdlib.get_logger(__name__)


# TODO this should be changed to use the actual FormExportOptions dataclass as input
# Something like https://stackoverflow.com/a/22520957 might work
@app.task(ignore_result=True)
@transaction.atomic()
def process_forms_export(
    forms_uuids: Collection[str], user_id: int, export_options: FormExportOptionsData
) -> None:
    user = User.objects.get(id=user_id)
    options = FormExportOptions(**export_options)

    filename = f"forms-export_{uuid4()}.zip"
    # start with an empty file and we'll write to it as we're exporting
    forms_export = FormsExport.objects.create(
        user=user, export_content=File(BytesIO(), name=filename)
    )
    with forms_export.export_content.open("wb") as outfile:
        export_multiple_forms(forms_uuids, export_options=options, target=outfile)

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


# TODO this should be changed to use the actual FormImportOptions dataclass as input
# Something like https://stackoverflow.com/a/22520957 might work
@app.task(ignore_result=True)
def process_forms_import(
    import_file: str, user_id: int, import_options: FormImportOptionsData
) -> None:
    storage = storages["privates"]
    failed_files: list[tuple[str, object]] = []
    # This deletes the temp dir once the context manager is exited
    with (
        tempfile.TemporaryDirectory() as temp_dir,
        zipfile.ZipFile(storage.open(import_file), "r") as zip_file,
    ):
        for zipped_form_file in zip_file.infolist():
            try:
                theme_uuid = import_options.get("theme_uuid")
                category_uuid = import_options.get("category_uuid")

                theme: Theme | None = (
                    Theme.objects.get(uuid=theme_uuid) if theme_uuid else None
                )
                category: Category | None = (
                    Category.objects.get(uuid=category_uuid) if category_uuid else None
                )

                # Get the form configuration import options. If not provided, use the
                # default of all form configuration options.
                form_configuration_options = import_options.get(
                    "form_configuration", list(FormConfigurationOptions)
                )
                # Get the additional form configuration import options. If not
                # provided, use the default of no additional form configuration.
                additional_form_configuration_options = import_options.get(
                    "additional_form_configuration", []
                )

                # This normalizes the path before extracting the files (to avoid writing outside the temp_dir)
                import_form(  # pyright: ignore[reportUnusedCallResult]
                    zip_file.extract(member=zipped_form_file, path=temp_dir),
                    FormImportOptions(
                        form_configuration=form_configuration_options,
                        additional_form_configuration=additional_form_configuration_options,
                        theme=theme,
                        category=category,
                    ),
                )
            except ValidationError as exc:
                filename = Path(zipped_form_file.filename).name
                failed_files.append((filename, exc.detail))
                logger.error("forms.import_failure", filename=filename, exc_info=exc)
                continue

    audit_logger.info("bulk_forms_imported", user_id=user_id, failed_files=failed_files)
    storage.delete(import_file)
