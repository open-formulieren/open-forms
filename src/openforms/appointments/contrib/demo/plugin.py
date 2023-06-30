from datetime import datetime, time

from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy as _

from openforms.formio.typing import Component

from ...base import (
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)
from ...registry import register


@register("demo")
class DemoAppointment(BasePlugin):
    verbose_name = _("Demo")
    is_demo_plugin = True

    def get_available_products(self, current_products=None):
        return [
            AppointmentProduct(identifier="1", name="Test product 1"),
            AppointmentProduct(identifier="2", name="Test product 2"),
        ]

    def get_locations(self, products=None):
        return [AppointmentLocation(identifier="1", name="Test location")]

    def get_dates(self, products, location, start_at=None, end_at=None):
        return [timezone.localdate()]

    def get_times(self, products, location, day):
        today = timezone.localdate()
        times = (time(12, 0), time(15, 15), time(15, 45))
        return [timezone.make_aware(datetime.combine(today, _time)) for _time in times]

    def get_required_customer_fields(
        self,
        products: list[AppointmentProduct],
    ) -> list[Component]:
        last_name: Component = {
            "type": "textfield",
            "key": "lastName",
            "label": gettext("Last name"),
        }
        return [last_name]

    def create_appointment(self, products, location, start_at, client, remarks=None):
        print(
            "Create appointment \n",
            f"products: {products}\n",
            f"location : {location}\n",
            f"start_at: {start_at}\n",
            f"client: {client}\n",
            f"remarks: {remarks}",
        )
        return "test 1"

    def delete_appointment(self, identifier: str) -> None:
        print(identifier)

    def get_appointment_details(self, identifier: str):
        return AppointmentDetails(
            identifier=identifier,
            products=[
                AppointmentProduct(identifier="1", name="Test product 1"),
                AppointmentProduct(identifier="2", name="Test product 2"),
            ],
            location=AppointmentLocation(identifier="1", name="Test location"),
            start_at=datetime(2021, 1, 1, 12, 0),
            end_at=datetime(2021, 1, 1, 12, 15),
            remarks="Remarks",
            other={"Some": "<h1>Data</h1>"},
        )

    def check_config(self):  # pragma: no cover
        """
        Demo config is always valid.
        """
        pass
