from datetime import date, datetime

from django.utils.translation import gettext_lazy as _

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

    def get_locations(self, products):
        return [AppointmentLocation(identifier="1", name="Test location")]

    def get_dates(self, products, location, start_at=None, end_at=None):
        return [date(2023, 1, 1)]

    def get_times(self, products, location, day):
        return [datetime(2023, 1, 1, 12, 0)]

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

    def check_config(self):
        """
        Demo config is always valid.
        """
        pass
