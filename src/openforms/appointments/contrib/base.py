import logging
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime

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
    code: str = None


@dataclass()
class AppointmentLocation:
    identifier: str
    name: str


@dataclass()
class AppointmentClient:
    last_name: str = None
    initials: str = None
    birthdate: date = None
    phonenumber: str = None


class BasePlugin:
    """
    Base Appointment plugin.
    """

    verbose_name = _("Set the 'verbose_name' attribute for a human-readable name")
    configuration_options = EmptyOptions

    def __init__(self, identifier: str):
        self.identifier = identifier

    # override

    def get_available_products(self, current_products: list = None) -> list:
        """
        Retrieve all available products and services to create an appointment
        for. You can pass `current_products` to only retrieve available
        products in combination with the `current_products`.

        @param current_products: List of `AppointmentProduct`, as obtained from another `get_available_products` call.
        @return: List of `AppointmentProduct`
        """
        raise NotImplementedError()

    def get_locations(self, products: list) -> list:
        """
        Retrieve all available locations for given `products`.

        @param products: List of `AppointmentProduct`, as obtained from `get_available_products`.
        @return: List of `AppointmentLocation`
        """
        raise NotImplementedError()

    def get_dates(
        self,
        products: list,
        location: AppointmentLocation,
        start_at: date = None,
        end_at: date = None,
    ) -> list:
        """
        Retrieve all available dates for given `products` and `location`.

        @param products: List of `AppointmentProduct`, as obtained from `get_available_products`.
        @param location: An `AppointmentLocation`, as obtained from `get_locations`.
        @param start_at: The start `date` to retrieve available dates for. Default: `date.today()`.
        @param end_at: The end `date` to retrieve available dates for. Default: 14 days after `start_date`.
        @return: List of `date`
        """
        raise NotImplementedError()

    def get_times(
        self, products: list, location: AppointmentLocation, day: date
    ) -> list:
        """
        Retrieve all available times for given `products`, `location` and `day`.

        @param products: List of `AppointmentProduct`, as obtained from `get_available_products`.
        @param location: An `AppointmentLocation`, as obtained from `get_locations`.
        @param day: A `date` to retrieve available times for.
        @return: List of `datetime`.
        """
        raise NotImplementedError()

    def get_calendar(
        self,
        products: list,
        location: AppointmentLocation,
        start_at: date = None,
        end_at: date = None,
    ) -> OrderedDict:
        """
        Retrieve a calendar.

        WARNING: This default implementation has significant performance issues.
        You can override this function with a more efficient implementation if
        the service supports it.

        @param products: List of `AppointmentProduct`, as obtained from `get_available_products`.
        @param location: An `AppointmentLocation`, as obtained from `get_locations`.
        @param start_at: The start `date` to retrieve available dates for. Default: `date.today()`.
        @param end_at: The end `date` to retrieve available dates for. Default: 14 days after `start_date`.
        @return: `OrderedDict` where each key represents a date and the values is a list of times.
        """
        days = self.get_dates(products, location, start_at, end_at)

        result = OrderedDict()

        try:
            for day in days:
                times = self.get_times(products, location, day)
                result[day] = times
        except Exception as e:
            logger.exception(e)
        finally:
            return result

    def create_appointment(
        self, products: list, location: AppointmentLocation, start_at: datetime = None
    ) -> str:
        """
        Create an appointment.

        @param products: List of `AppointmentProduct`, as obtained from `get_available_products`.
        @param location: An `AppointmentLocation`, as obtained from `get_locations`.
        @param start_at: A `datetime` to start the appointment, as obtained from `get_calendar`.
        @return: An appointment identifier as `str`.
        """
        raise NotImplementedError()

    def delete_appointment(self, identifier: str) -> bool:
        """
        Delete an appointment.

        @param identifier: A `str` that represents the unique identification of the appointment.
        @return: `True` if succesful, `False` otherwise.
        """
        raise NotImplementedError()

    # cosmetics

    def get_label(self) -> str:
        return self.verbose_name
