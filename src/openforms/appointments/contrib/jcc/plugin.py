import logging
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from functools import wraps
from typing import Callable, List, Optional, ParamSpec, TypeVar

from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from requests.exceptions import RequestException
from zeep.client import Client
from zeep.exceptions import Error as ZeepError
from zgw_consumers.concurrent import parallel

from openforms.formio.typing import Component
from openforms.plugins.exceptions import InvalidPluginConfiguration

from ...base import (
    AppointmentClient,
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)
from ...exceptions import (
    AppointmentCreateFailed,
    AppointmentDeleteFailed,
    AppointmentException,
)
from ...registry import register
from ...utils import create_base64_qrcode
from .client import get_client
from .constants import FIELD_TO_FORMIO_COMPONENT, CustomerFields
from .exceptions import GracefulJCCError, JCCError
from .models import JccConfig

logger = logging.getLogger(__name__)


def squash_ids(lst):
    return ",".join([i.identifier for i in lst])


@contextmanager
def log_soap_errors(template: str, *args):
    try:
        yield
    except (ZeepError, RequestException) as e:
        logger.exception(template, *args, exc_info=e)
        raise GracefulJCCError("SOAP call failed") from e
    except Exception as exc:
        raise JCCError from exc


Param = ParamSpec("Param")
T = TypeVar("T")
FuncT = Callable[Param, T]


def with_graceful_default(default: T):
    def decorator(func: FuncT) -> FuncT:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except GracefulJCCError:
                return default

        return wrapper

    return decorator


@register("jcc")
class JccAppointment(BasePlugin):
    """
    Plugin for JCC-Afspraken internetafsprakenadapter GGS2 (april 2020)

    Website: https://www.jccsoftware.nl/
    """

    verbose_name = _("JCC")

    @with_graceful_default(default=[])
    def get_available_products(
        self,
        current_products: list[AppointmentProduct] | None = None,
        location_id: str = "",
    ) -> list[AppointmentProduct]:
        if location_id:
            logger.debug(
                "Plugin does not support filtering products by location.",
                extra={"location_id": location_id},
            )

        client = get_client()
        with log_soap_errors("Could not retrieve available products"):
            if current_products:
                current_product_ids = squash_ids(current_products)
                result = client.service.getGovAvailableProductsByProduct(
                    ProductNr=current_product_ids
                )
            else:
                result = client.service.getGovAvailableProducts()

        return [
            AppointmentProduct(
                entry["productId"], entry["productDesc"], entry["productCode"]
            )
            for entry in result
        ]

    def _get_all_locations(self, client: Client) -> list[AppointmentLocation]:
        with log_soap_errors("Could not retrieve location IDs"):
            location_ids = client.service.getGovLocations()
            with parallel() as pool:
                details = pool.map(
                    lambda location_id: client.service.getGovLocationDetails(
                        locationID=location_id
                    ),
                    location_ids,
                )
            # evaluate the generator
            details = list(details)

        locations = [
            AppointmentLocation(
                identifier=identifier,
                name=entry["locationDesc"],
                address=entry["address"],
                postalcode=entry["postalcode"],
                city=entry["city"],
            )
            for identifier, entry in zip(location_ids, details)
        ]

        return locations

    @with_graceful_default(default=[])
    def get_locations(
        self,
        products: list[AppointmentProduct] | None = None,
    ) -> list[AppointmentLocation]:
        client = get_client()
        if products is None:
            return self._get_all_locations(client)

        product_ids = squash_ids(products)
        with log_soap_errors(
            "Could not retrieve locations for products '%s'", product_ids
        ):
            result = client.service.getGovLocationsForProduct(productID=product_ids)

        return [
            AppointmentLocation(entry["locationID"], entry["locationDesc"])
            for entry in result
        ]

    @with_graceful_default(default=[])
    def get_dates(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        start_at: Optional[date] = None,
        end_at: Optional[date] = None,
    ) -> List[date]:
        client = get_client()
        product_ids = squash_ids(products)

        start_at = start_at or date.today()
        end_at = end_at or (start_at + timedelta(days=14))

        with log_soap_errors(
            "Could not retrieve dates for products '%s' at location '%s' between %s - %s",
            product_ids,
            location,
            start_at,
            end_at,
        ):
            max_end_date = client.service.getGovLatestPlanDate(productId=product_ids)
            if end_at > max_end_date:
                end_at = max_end_date

            days = client.service.getGovAvailableDays(
                locationID=location.identifier,
                productID=product_ids,
                startDate=start_at,
                endDate=end_at,
                appDuration=0,
            )
            return days

    @with_graceful_default(default=[])
    def get_times(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        day: date,
    ) -> List[datetime]:
        product_ids = squash_ids(products)

        client = get_client()
        with log_soap_errors(
            "Could not retrieve times for products '%s' at location '%s' on %s",
            product_ids,
            location,
            day,
        ):
            return client.service.getGovAvailableTimesPerDay(
                date=day,
                productID=product_ids,
                locationID=location.identifier,
                appDuration=0,
            )

    @with_graceful_default(default=[])
    def get_required_customer_fields(
        self,
        products: list[AppointmentProduct],
    ) -> list[Component]:
        product_ids = squash_ids(products)

        client = get_client()
        with log_soap_errors(
            "Could not retrieve required fields for products '%s'", product_ids
        ):
            field_names = client.service.GetRequiredClientFields(productID=product_ids)

        last_name = FIELD_TO_FORMIO_COMPONENT[CustomerFields.last_name]
        return [last_name] + [FIELD_TO_FORMIO_COMPONENT[field] for field in field_names]

    def create_appointment(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        start_at: datetime,
        client: AppointmentClient,
        remarks: str = "",
    ) -> str:
        product_ids = squash_ids(products)

        jcc_client = get_client()
        try:
            factory = jcc_client.type_factory("http://www.genericCBS.org/GenericCBS/")
            appointment_details = factory.AppointmentDetailsType(
                locationID=location.identifier,
                productID=product_ids,
                clientLastName=client.last_name,
                clientDateOfBirth=client.birthdate,
                appStartTime=start_at,
                appEndTime=start_at,  # Required but unused by the service.
                isClientVerified=False,
                isRecurring=False,
                # Phone number is often required for appointment,
                # use fake phone number if no client phone number
                clientTel=client.phonenumber or "0123456789",
                # Optional fields.
                # These might be needed. Depends on `GetRequiredClientFields`
                #
                # clientID=bsn,
                # clientSex="M/F",
                # clientInitials="",
                # clientAddress="",
                # clientPostalCode="",
                # clientCity="",
                # clientCountry="",
                # clientMail="",
                appointmentDesc=remarks,
                # caseID": "",
            )

            result = jcc_client.service.bookGovAppointment(
                appDetail=appointment_details, fields=[]
            )

            if result["updateStatus"] == 0:
                return result["appID"]
            else:
                raise AppointmentCreateFailed(
                    "Could not create appointment for products '%s' at location '%s' starting at %s (updateStatus=%s)",
                    product_ids,
                    location,
                    start_at,
                    result["updateStatus"],
                )
        except (ZeepError, RequestException, KeyError) as e:
            raise AppointmentCreateFailed(e)

    def delete_appointment(self, identifier: str) -> None:
        client = get_client()
        try:
            result = client.service.deleteGovAppointment(appID=identifier)

            if result != 0:
                raise AppointmentDeleteFailed(
                    "Could not delete appointment: %s (updateStatus=%s)",
                    identifier,
                    result,
                )
        except (ZeepError, RequestException) as e:
            raise AppointmentDeleteFailed(e)

    def get_appointment_details(self, identifier: str) -> AppointmentDetails:
        client = get_client()
        try:
            # NOTE: The operation `getGovAppointmentExtendedDetails` seems
            # missing. This would include the product descriptions but now we
            # need to make an additional call to get those.
            details = client.service.getGovAppointmentDetails(appID=identifier)
            if details is None:
                raise AppointmentException("No appointment details could be retrieved.")

            location = client.service.getGovLocationDetails(
                locationID=details.locationID
            )
            qrcode = client.service.GetAppointmentQRCodeText(appID=identifier)

            app_products = []
            for pid in details.productID.split(","):
                product = client.service.getGovProductDetails(productID=pid)

                app_products.append(
                    AppointmentProduct(identifier=pid, name=product.description)
                )

            qrcode_base64 = create_base64_qrcode(qrcode)

            qr_label = _("QR-code")
            qr_value = format_html(
                '<img src="data:image/png;base64,{qrcode_base64}" alt="{qrcode}" />',
                qrcode_base64=qrcode_base64,
                qrcode=qrcode,
            )

            result = AppointmentDetails(
                identifier=identifier,
                products=app_products,
                location=AppointmentLocation(
                    identifier=details.locationID,
                    name=location.locationDesc,
                    address=location.address,
                    postalcode=location.postalcode,  # Documentation says `postalCode`
                    city=location.city,
                ),
                start_at=details.appStartTime,
                end_at=details.appEndTime,
                remarks=details.appointmentDesc,
                other={qr_label: qr_value},
            )

            return result

        except (ZeepError, RequestException, AttributeError) as e:
            raise AppointmentException(e)

    def check_config(self):
        client = get_client()
        try:
            client.service.getGovAvailableProducts()
        except (ZeepError, RequestException) as e:
            raise InvalidPluginConfiguration(
                _("Invalid response: {exception}").format(exception=e)
            )

    def get_config_actions(self):
        return [
            (
                _("Configuration"),
                reverse(
                    "admin:jcc_jccconfig_change",
                    args=(JccConfig.singleton_instance_id,),
                ),
            ),
        ]
