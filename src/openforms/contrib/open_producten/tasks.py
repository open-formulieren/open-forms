import io
import logging

from django.core.management import call_command

from openforms.celery import app

logger = logging.getLogger(__name__)


@app.task()
def import_product_type_prices():
    logger.info("starting import_prices() task")

    out = io.StringIO()

    call_command("import_prices", stdout=out)

    logger.info("finished import_prices() task")

    return out.getvalue()
