import os

from django.conf import settings

from stuf.tests.factories import SoapServiceFactory

from ..contrib.jcc.models import JccConfig
from ..models import AppointmentsConfig


def setup_jcc() -> None:
    appointments_config = AppointmentsConfig.get_solo()
    appointments_config.config_path = (
        "openforms.appointments.contrib.jcc.models.JccConfig"
    )
    appointments_config.save()

    config = JccConfig.get_solo()
    wsdl = os.path.abspath(
        os.path.join(
            settings.DJANGO_PROJECT_DIR,
            "appointments/contrib/jcc/tests/mock/GenericGuidanceSystem2.wsdl",
        )
    )
    config.service = SoapServiceFactory.create(url=wsdl)
    config.save()
