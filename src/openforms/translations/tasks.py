import json
from zoneinfo import ZoneInfo

from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import structlog
from celery_once import QueueOnce

from openforms.celery import app

from .constants import StatusChoices
from .models import TranslationsMetaData
from .subprocesses import compile_messages_file

logger = structlog.stdlib.get_logger(__name__)


@app.task(base=QueueOnce, once={"graceful": True})
def process_custom_translation_assets(translations_metadata_pk: str) -> None:
    """
    Celery task for processing custom translations JSON file.

    The task is triggered by the admin page when the TranslationsMetaData instance is
    saved. Checks if the file is in valid JSON format and triggers the compiling. All
    related db fields are updated according the successful or not state of the compiling.
    """
    instance = TranslationsMetaData.objects.get(pk=translations_metadata_pk)
    file = instance.messages_file.file

    log = logger.bind(
        action="translations.process_custom_translations_asset",
        translation_metadata_id=instance.pk,
        input_file_name=instance.messages_file.file.name,
    )

    instance.processing_status = StatusChoices.in_progress
    instance.debug_output = ""
    instance.save(update_fields=("processing_status", "debug_output"))

    log.info("custom_translations_file_processing_started")

    # make sure the uploaded file can be serialized before starting the subprocess
    try:
        json.load(file)
    except json.JSONDecodeError as e:
        instance.debug_output = _(
            "JSON parsing failed (the file should be in a valid JSON format): {error}"
        ).format(error=e.args[0])
        instance.processing_status = StatusChoices.failed
        instance.save(
            update_fields=(
                "processing_status",
                "debug_output",
            )
        )
        log.error("custom_translations_file_processing_failed")
        return

    # the file is a valid JSON file, begin the subprocess
    log.info("custom_translations_file_compiling_started")
    success, result = compile_messages_file(instance.messages_file.path)

    if success:
        log.info("custom_translations_file_compiling_succeeded")

        instance.processing_status = StatusChoices.done
        instance.debug_output = ""
        instance.last_updated = timezone.now().astimezone(ZoneInfo("Europe/Amsterdam"))

        assert result is not None

        instance.compiled_asset.save(
            "compiled_asset.json", ContentFile(result), save=False
        )

        compiled_data = json.loads(result)
        instance.messages_count = len(compiled_data)
    else:
        log.error("custom_translations_file_processing_failed")

        instance.processing_status = StatusChoices.failed
        instance.debug_output = result or ""

    instance.save()
