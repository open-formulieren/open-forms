from soap.tests.factories import SoapServiceFactory

from ..contrib.jcc.models import JccConfig
from ..contrib.jcc.tests.utils import WSDL
from ..models import AppointmentsConfig


# FIXME: replace with proper mocks, see ../contrib/jcc/tests/utils.py
def setup_jcc() -> None:
    appointments_config = AppointmentsConfig.get_solo()
    appointments_config.plugin = "jcc"
    appointments_config.save()

    config = JccConfig.get_solo()
    config.service = SoapServiceFactory.create(url=str(WSDL))
    config.save()
