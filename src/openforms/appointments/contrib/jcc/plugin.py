import logging
from collections import OrderedDict
from datetime import date, datetime, timedelta
from typing import OrderedDict

from zeep import Client

from ..base import (
    AppointmentClient,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)

logger = logging.getLogger(__name__)


def squash_ids(lst):
    return ",".join([i.identifier for i in lst])


class Plugin(BasePlugin):
    """
    Plugin for JCC-Afspraken internetafsprakenadapter GGS2 (april 2020)
    """

    def __init__(self):
        self.client = None
        # self.client = Client(
        #     "TODO: <from settings>"
        # )

    def get_available_products(self, current_products: list = None) -> list:
        try:
            if current_products:
                current_product_ids = squash_ids(current_products)
                result = self.client.service.getGovAvailableProductsByProduct(
                    ProductNr=current_product_ids
                )
            else:
                result = self.client.service.getGovAvailableProducts()
        except Exception as e:
            logger.exception(e)
            return []

        return [
            AppointmentProduct(
                entry["productId"], entry["productDesc"], entry["productCode"]
            )
            for entry in result
        ]

    def get_locations(self, products: list) -> list:
        product_ids = squash_ids(products)

        try:
            result = self.client.service.getGovLocationsForProduct(
                productID=product_ids
            )
        except Exception as e:
            logger.exception(e)
            return []

        return [
            AppointmentLocation(entry["locationID"], entry["locationDesc"])
            for entry in result
        ]

    def get_dates(
        self,
        products: list,
        location: AppointmentLocation,
        start_at: date = None,
        end_at: date = None,
    ) -> list:
        product_ids = squash_ids(products)

        if not start_at:
            start_at = date.today()
        if not end_at:
            end_at = start_at + timedelta(days=14)

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
        except Exception as e:
            logger.exception(e)
            return []

    def get_times(
        self, products: list, location: AppointmentLocation, day: date
    ) -> list:
        product_ids = squash_ids(products)

        try:
            times = self.client.service.getGovAvailableTimesPerDay(
                date=day,
                productID=product_ids,
                locationID=location.identifier,
                appDuration=0,
            )
            return times
        except Exception as e:
            logger.exception(e)
            return []

    def get_calendar(
        self,
        products: list,
        location: AppointmentLocation,
        start_at: date = None,
        end_at: date = None,
    ) -> OrderedDict:
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
        self,
        products: list,
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
                raise Exception(
                    "Could not create appointment (updateStatus=%s)",
                    result["updateStatus"],
                )

        except Exception as e:
            logger.exception(e)
            raise
