import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from requests.exceptions import RequestException
from zeep import Client
from zeep.exceptions import Error as ZeepError

from ...base import (
    AppointmentClient,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)
from ...exceptions import (
    AppointmentCreateFailed,
    AppointmentDeleteFailed,
    AppointmentException,
)

logger = logging.getLogger(__name__)


def squash_ids(lst):
    return ",".join([i.identifier for i in lst])


class Plugin(BasePlugin):
    """
    Plugin for JCC-Afspraken internetafsprakenadapter GGS2 (april 2020)

    Website: https://www.jccsoftware.nl/
    """

    def __init__(self):
        self.client = None
        # self.client = Client(
        #     "TODO: <from settings>"
        # )

    def get_available_products(
        self, current_products: Optional[List[AppointmentProduct]] = None
    ) -> List[AppointmentProduct]:
        try:
            if current_products:
                current_product_ids = squash_ids(current_products)
                result = self.client.service.getGovAvailableProductsByProduct(
                    ProductNr=current_product_ids
                )
            else:
                result = self.client.service.getGovAvailableProducts()
        except (ZeepError, RequestException) as e:
            logger.exception("Could not retrieve available products", exc_info=e)
            return []
        except Exception as exc:
            raise AppointmentException from exc

        return [
            AppointmentProduct(
                entry["productId"], entry["productDesc"], entry["productCode"]
            )
            for entry in result
        ]

    def get_locations(
        self, products: List[AppointmentProduct]
    ) -> List[AppointmentLocation]:
        product_ids = squash_ids(products)

        try:
            result = self.client.service.getGovLocationsForProduct(
                productID=product_ids
            )
        except (ZeepError, RequestException) as e:
            logger.exception(
                "Could not retrieve locations for products '%s'",
                product_ids,
                exc_info=e,
            )
            return []
        except Exception as exc:
            raise AppointmentException from exc

        return [
            AppointmentLocation(entry["locationID"], entry["locationDesc"])
            for entry in result
        ]

    def get_dates(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        start_at: Optional[date] = None,
        end_at: Optional[date] = None,
    ) -> List[date]:
        product_ids = squash_ids(products)

        start_at = start_at or date.today()
        end_at = end_at or (start_at + timedelta(days=14))

        try:
            max_end_date = self.client.service.getGovLatestPlanDate(
                productId=product_ids
            )
            if end_at > max_end_date:
                end_at = max_end_date

            days = self.client.service.getGovAvailableDays(
                locationID=location.identifier,
                productID=product_ids,
                startDate=start_at,
                endDate=end_at,
                appDuration=0,
            )
            return days
        except (ZeepError, RequestException) as e:
            logger.exception(
                "Could not retrieve dates for products '%s' at location '%s' between %s - %s",
                product_ids,
                location,
                start_at,
                end_at,
                exc_info=e,
            )
            return []
        except Exception as exc:
            raise AppointmentException from exc

    def get_times(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        day: date,
    ) -> List[datetime]:
        product_ids = squash_ids(products)

        try:
            times = self.client.service.getGovAvailableTimesPerDay(
                date=day,
                productID=product_ids,
                locationID=location.identifier,
                appDuration=0,
            )
            return times
        except (ZeepError, RequestException) as e:
            logger.exception(
                "Could not retrieve times for products '%s' at location '%s' on %s",
                product_ids,
                location,
                day,
                exc_info=e,
            )
            return []
        except Exception as exc:
            raise AppointmentException from exc

    def create_appointment(
        self,
        products: List[AppointmentProduct],
        location: AppointmentLocation,
        start_at: datetime,
        client: AppointmentClient,
        remarks: str = None,
    ) -> str:
        product_ids = squash_ids(products)

        try:
            factory = self.client.type_factory("http://www.genericCBS.org/GenericCBS/")
            appointment_details = factory.AppointmentDetailsType(
                locationID=location.identifier,
                productID=product_ids,
                clientLastName=client.last_name,
                clientDateOfBirth=client.birthdate,
                appStartTime=start_at,
                appEndTime=start_at,  # Needed but unused by the service.
                isClientVerified=False,
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
                # clientTel="",
                # clientMail="",
                appointmentDesc=remarks,
                # caseID": "",
            )

            result = self.client.service.bookGovAppointment(
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
        try:
            result = self.client.service.deleteGovAppointment(appID=identifier)

            if result != 0:
                raise AppointmentDeleteFailed(
                    "Could not delete appointment (updateStatus=%s)",
                    result,
                )
        except (ZeepError, RequestException, KeyError) as e:
            raise AppointmentDeleteFailed(e)
