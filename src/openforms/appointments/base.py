from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Generic, TypeAlias, TypeVar

from django.db.models import TextChoices
from django.urls import reverse

from rest_framework import serializers

from openforms.formio.typing import Component
from openforms.plugins.plugin import AbstractBasePlugin
from openforms.submissions.models import Submission
from openforms.typing import JSONPrimitive
from openforms.utils.mixins import JsonSchemaSerializerMixin
from openforms.utils.urls import build_absolute_uri

from .tokens import submission_appointment_token_generator


class EmptyOptions(JsonSchemaSerializerMixin, serializers.Serializer):
    pass


@dataclass()
class Product:
    identifier: str
    name: str
    code: str = ""
    amount: int = 1

    def __str__(self):
        return f"{self.identifier} x {self.amount}"


@dataclass()
class Location:
    identifier: str
    name: str
    address: str | None = None
    postalcode: str | None = None
    city: str | None = None

    def __str__(self):
        return self.identifier


F = TypeVar("F", bound=TextChoices)
# generic type for the plugin-specific enum of field names


@dataclass
class CustomerDetails(Generic[F]):
    # these should realistically only be string values, as they are user input stored as JSON.
    details: dict[F, JSONPrimitive]


TInput = TypeVar("TInput", bound=JSONPrimitive)
Normalizer: TypeAlias = Callable[[TInput], TInput]


@dataclass()
class AppointmentDetails:
    identifier: str
    products: list[Product]
    location: Location
    start_at: datetime
    end_at: datetime | None = None
    remarks: str | None = None

    # These are typically key/values-pairs where both the key and value are
    # considered *not* to be HTML-safe. Plugins need to explicitly mark trusted
    # data as safe.
    other: dict | None = None

    def __str__(self):
        return self.identifier


class BasePlugin(Generic[F], ABC, AbstractBasePlugin):
    """
    Base Appointment plugin.
    """

    configuration_options = EmptyOptions
    supports_multiple_products: bool = False
    normalizers: dict[F, list[Normalizer]] = {}

    @abstractmethod
    def get_available_products(
        self,
        current_products: list[Product] | None = None,
        location_id: str = "",
    ) -> list[Product]:
        """
        Retrieve all available products and services to create an appointment for.

        You can pass ``current_products`` to only retrieve available
        products in combination with the ``current_products``.

        :param current_products: List of :class:`Product`, as obtained from
          another :meth:`get_available_products` call.
        :param location_id: ID of the location to filter products on - plugins may
          support this.
        :returns: List of :class:`Product`
        """
        raise NotImplementedError()

    @abstractmethod
    def get_locations(
        self,
        products: list[Product] | None = None,
    ) -> list[Location]:
        """
        Retrieve all available locations.

        :param products: List of :class:`Product`, as obtained from
          :meth:`get_available_products`. If ``None`` or unspecified, all possible
          locations are returned. Otherwise, if the plugin supports it, locations are
          filtered given the products.
        :returns: List of :class:`Location`
        """
        raise NotImplementedError()

    @abstractmethod
    def get_dates(
        self,
        products: list[Product],
        location: Location,
        start_at: date | None = None,
        end_at: date | None = None,
    ) -> list[date]:
        """
        Retrieve all available dates for given ``products`` and ``location``.

        :param products: List of :class:`Product`, as obtained from :meth:`get_available_products`.
        :param location: An :class:`Location`, as obtained from :meth:`get_locations`.
        :param start_at: The start :class:`date` to retrieve available dates for. Default: ``date.today()``.
        :param end_at: The end :class:`date` to retrieve available dates for. Default: 14 days after ``start_date``.
        :returns: List of :class:`date`
        """
        raise NotImplementedError()

    @abstractmethod
    def get_times(
        self,
        products: list[Product],
        location: Location,
        day: date,
    ) -> list[datetime]:
        """
        Retrieve all available times for given ``products``, ``location`` and ``day``.

        :param products: List of :class:`Product`, as obtained from `get_available_products`.
        :param location: An :class:`Location`, as obtained from `get_locations`.
        :param day: A :class:`date` to retrieve available times for.
        :returns: List of available :class:`datetime`.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_required_customer_fields(
        self,
        products: list[Product],
    ) -> list[Component]:
        """
        Given a list of products, return the additional required customer fields.

        The fields are returned as a Form.io components array, including possible useful
        autocomplete attributes. This should make it easy to render the fields using
        existing tooling.
        """
        raise NotImplementedError()

    def normalize_contact_details(
        self, data: dict[F, JSONPrimitive]
    ) -> dict[F, JSONPrimitive]:
        # XXX: We could consider using openforms.formio.service.normalize_value_for_component,
        # but there currently is no phone normalizer and adding it could potentially break this
        # component...
        normalized = {}
        for key, value in data.items():
            for normalizer in self.normalizers.get(key, []):
                value = normalizer(value)
            normalized[key] = value
        return normalized

    @abstractmethod
    def create_appointment(
        self,
        products: list[Product],
        location: Location,
        start_at: datetime,
        client: CustomerDetails[F],
        remarks: str = "",
    ) -> str:
        """
        Create an appointment.

        :param products: List of :class:`Product`, as obtained from :meth:`get_available_products`.
        :param location: An :class:`Location`, as obtained from :meth:`get_locations`.
        :param start_at: A `datetime` to start the appointment, as obtained from :meth:`get_dates`.
        :param client: A :class:`CustomerDetails` that holds client details.
        :param remarks: A ``str`` for additional remarks, added to the appointment.
        :returns: An appointment identifier as ``str``.
        :raises AppointmentCreateFailed: If the appointment could not be created.
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_appointment(self, identifier: str) -> None:
        """
        Delete an appointment.

        :param identifier: A string that represents the unique identification of the appointment.
        :raises AppointmentDeleteFailed: If the appointment could not be deleted.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_appointment_details(self, identifier: str) -> AppointmentDetails:
        """
        Get appointment details.

        :param identifier: A string that represents the unique identification of the appointment.
        :returns: :class:`AppointmentDetails`.
        """
        raise NotImplementedError()

    # cosmetics

    @staticmethod
    def get_cancel_link(submission: Submission) -> str:
        token = submission_appointment_token_generator.make_token(submission)

        path = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": token,
                "submission_uuid": submission.uuid,
            },
        )

        return build_absolute_uri(path)
