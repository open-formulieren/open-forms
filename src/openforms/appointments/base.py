import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, List, Optional

from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from openforms.utils.mixins import JsonSchemaSerializerMixin


class EmptyOptions(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


logger = logging.getLogger(__name__)


@dataclass()
class AppointmentProduct:
    identifier: str
    name: str
    code: Optional[str] = None

    def __str__(self):
        return self.identifier


@dataclass()
class AppointmentLocation:
    identifier: str
    name: str
    address: Optional[str] = None
    postalcode: Optional[str] = None
    city: Optional[str] = None

    def __str__(self):
        return self.identifier


@dataclass()
class AppointmentClient:
    last_name: str
    birthdate: date
    initials: Optional[str] = None
    phonenumber: Optional[str] = None

    def __str__(self):
        return self.last_name


@dataclass()
class AppointmentDetails:
    identifier: str
    products: List[AppointmentProduct]
    location: AppointmentLocation
    start_at: datetime
    end_at: Optional[datetime] = None
    remarks: Optional[str] = None

    # These are typically key/values-pairs where both the key and value are
    # considered to be HTML-safe and suited to show to end users.
    other: Optional[dict] = None

    def __str__(self):
        return self.identifier


class BasePlugin:
    """
    Base Appointment plugin.
    """

    verbose_name = _("Set the 'verbose_name' attribute for a human-readable name")
    configuration_options = EmptyOptions

    # override

    def get_available_products(
        self, current_products: Optional[List[AppointmentProduct]] = None
    ) -> List[AppointmentProduct]:
        """
        Retrieve all available products and services to create an appointment for.

        You can pass ``current_products`` to only retrieve available
        products in combination with the ``current_products``.

        :param current_products: List of :class:`AppointmentProduct`, as obtained from
          another :meth:`get_available_products` call.
        :returns: List of :class:`AppointmentProduct`
        """
        raise NotImplementedError()

    def get_locations(
        self, products: List[AppointmentProduct]
    ) -> List[AppointmentLocation]:
        """
        Retrieve all available locations for given ``products``.

        :param products: List of :class:`AppointmentProduct`, as obtained from
          :meth:`get_available_products`. :returns: List of :class:`AppointmentLocation`
        """
        raise NotImplementedError()

    def get_dates(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        start_at: Optional[date] = None,
        end_at: Optional[date] = None,
    ) -> List[date]:
        """
        Retrieve all available dates for given ``products`` and ``location``.

        :param products: List of :class:`AppointmentProduct`, as obtained from :meth:`get_available_products`.
        :param location: An :class:`AppointmentLocation`, as obtained from :meth:`get_locations`.
        :param start_at: The start :class:`date` to retrieve available dates for. Default: ``date.today()``.
        :param end_at: The end :class:`date` to retrieve available dates for. Default: 14 days after ``start_date``.
        :returns: List of :class:`date`
        """
        raise NotImplementedError()

    def get_times(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        day: date,
    ) -> List[datetime]:
        """
        Retrieve all available times for given ``products``, ``location`` and ``day``.

        :param products: List of :class:`AppointmentProduct`, as obtained from `get_available_products`.
        :param location: An :class:`AppointmentLocation`, as obtained from `get_locations`.
        :param day: A :class:`date` to retrieve available times for.
        :returns: List of available :class:`datetime`.
        """
        raise NotImplementedError()

    def get_calendar(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        start_at: Optional[date] = None,
        end_at: Optional[date] = None,
    ) -> Dict[date, List[datetime]]:
        """
        Retrieve a calendar.

        WARNING: This default implementation has significant performance issues.
        You can override this function with a more efficient implementation if
        the service supports it.

        :param products: List of :class:`AppointmentProduct`, as obtained from :meth:`get_available_products`.
        :param location: An :class:`AppointmentLocation`, as obtained from :meth:`get_locations`.
        :param start_at: The start :class:`date` to retrieve available dates for. Default: ``date.today()``.
        :param end_at: The end :class:`date` to retrieve available dates for. Default: 14 days after ``start_date``.
        :returns: Dict where each key represents a date and the values is a list of times.
        """
        days = self.get_dates(products, location, start_at, end_at)

        result = {}

        for day in days:
            times = self.get_times(products, location, day)
            result[day] = times

        return result

    def create_appointment(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        start_at: datetime,
        client: AppointmentClient,
        remarks: str = None,
    ) -> str:
        """
        Create an appointment.

        :param products: List of :class:`AppointmentProduct`, as obtained from :meth:`get_available_products`.
        :param location: An :class:`AppointmentLocation`, as obtained from :meth:`get_locations`.
        :param start_at: A `datetime` to start the appointment, as obtained from :meth:`get_calendar`.
        :param client: A :class:`AppointmentClient` that holds client details.
        :param remarks: A ``str`` for additional remarks, added to the appointment.
        :returns: An appointment identifier as ``str``.
        :raises AppointmentCreateFailed: If the appoinment could not be created.
        """
        raise NotImplementedError()

    def delete_appointment(self, identifier: str) -> None:
        """
        Delete an appointment.

        :param identifier: A string that represents the unique identification of the appointment.
        :raises AppointmentDeleteFailed: If the appoinment could not be deleted.
        """
        raise NotImplementedError()

    def get_appointment_details(self, identifier: str) -> str:
        """
        Get appointment details.

        :param identifier: A string that represents the unique identification of the appointment.
        :returns: :class:`AppointmentDetails`.
        """
        raise NotImplementedError()

    # cosmetics

    def get_label(self) -> str:
        return self.verbose_name

    def get_appointment_details_html(self, identifier: str) -> str:
        """
        Returns an HTML version of the appointment details that can be used in
        a mail or webpage.
        """
        details = self.get_appointment_details(identifier)

        return render_to_string(
            "appointments/appointment_details.html", {"appointment": details}
        )
