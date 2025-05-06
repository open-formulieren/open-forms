from typing import Literal

from django.core import management

import structlog

from ..celery import app

logger = structlog.stdlib.get_logger(__name__)

type Command = Literal["clearsessions", "clean_cspreports", "delete_export_files"]


@app.task(ignore_result=True)
def run_management_command(*, command: Command) -> None:
    log = logger.bind(command=command)
    log.debug("start")
    management.call_command(command)
    log.debug("done")
