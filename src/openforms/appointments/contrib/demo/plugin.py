from datetime import datetime, time

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext, gettext_lazy as _

from openforms.formio.typing import Component

from ...base import (
    AppointmentDetails,
    BasePlugin,
    Location,
    Product,
)
from ...registry import register


class CustomerFields(models.TextChoices):
    last_name = "lastName", "Last name"
    first_name = "firstName", "First name"
    initials = "initials", "Initials"


def get_initials(name_or_initials: str) -> str:
    parts = [part for part in name_or_initials.split(" ") if part.strip()]
    return " ".join([f"{part[0]}." for part in parts])


@register("demo")
class DemoAppointment(BasePlugin[CustomerFields]):
    verbose_name = _("Demo")
    is_demo_plugin = True
    normalizers = {
        CustomerFields.initials: [get_initials],
    }

    def get_available_products(self, current_products=None, location_id: str = ""):
        return [
            Product(identifier="1", name="Test product 1"),
            Product(identifier="2", name="Test product 2"),
        ]

    def get_locations(self, products=None):
        return [Location(identifier="1", name="Test location")]

    def get_dates(self, products, location, start_at=None, end_at=None):
        return [timezone.localdate()]

    def get_times(self, products, location, day):
        today = timezone.localdate()
        times = (time(12, 0), time(15, 15), time(15, 45), time(17, 45))
        return [timezone.make_aware(datetime.combine(today, _time)) for _time in times]

    def get_required_customer_fields(
        self,
        products: list[Product],
    ) -> tuple[list[Component], None]:
        last_name: Component = {
            "type": "textfield",
            "key": "lastName",
            "label": gettext("Last name"),
            "validate": {
                "required": True,
                "maxLength": 20,
            },
        }
        email: Component = {
            "type": "email",
            "key": "email",
            "label": gettext("Email"),
            "validate": {
                "required": True,
                "maxLength": 100,
            },
        }
        components = [last_name, email]
        return components, None

    def create_appointment(self, products, location, start_at, client, remarks=""):
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
                Product(identifier="1", name="Test product 1"),
                Product(identifier="2", name="Test product 2"),
            ],
            location=Location(
                identifier="1", name="Test location", address="Test address"
            ),
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
