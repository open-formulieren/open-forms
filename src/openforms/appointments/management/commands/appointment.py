from datetime import date

from django.core.management import BaseCommand
from django.core.management.base import CommandError
from django.utils.module_loading import import_string

from openforms.appointments.base import AppointmentClient
from openforms.appointments.constants import AppointmentsConfigPaths
from openforms.appointments.utils import get_client

TIME_PARSE_FORMAT = "%H:%M"
DATE_PARSE_FORMAT = "%Y-%m-%d"


class Command(BaseCommand):
    help = "Perform various appointment plugin calls."

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--plugin",
            help="Enforce a specific plugin to be used. Defaults to the configured plugin.",
        )

    def handle(self, **options):
        plugin = options.get("plugin", None)
        if plugin:
            available_plugins = {c[1]: c[0] for c in AppointmentsConfigPaths.choices}
            if plugin not in available_plugins:
                raise CommandError(
                    f"Invalid plugin: {plugin}. Choices are: {available_plugins.keys()}"
                )
            config_class = import_string(available_plugins[plugin])
            self.client = config_class.get_solo().get_client()
        else:
            self.client = get_client()

        self.stdout.write(f"Using plugin: {plugin}")

        available_actions = [
            ("Create booking", "create_booking"),
            ("Get booking details", "show_booking"),
            ("Cancel booking", "cancel_booking"),
            ("Quit", "exit"),
        ]
        selected_action = self._show_options(
            available_actions, lambda x: x[0], "action"
        )

        func = getattr(self, selected_action[1])
        func()

    def _show_options(self, data, repr_func, obj_name, allow_multi=False):
        self.stdout.write(f"Available {obj_name}s:")

        available_options = {str(index + 1): entry for index, entry in enumerate(data)}

        for index, entry in available_options.items():
            val = repr_func(entry)
            self.stdout.write(f"[{index}] {val}")

        if allow_multi:
            msg = f"Choose one or more {obj_name}s (comma separated): "
        else:
            msg = f"Choose a {obj_name}: "

        while True:
            selected_option = input(msg)

            if allow_multi:
                selected_options = [o.strip() for o in selected_option.split(",")]
                if not set(selected_options).issubset(set(available_options.keys())):
                    self.stderr.write("Not all provided values are valid options.")
                else:
                    return [available_options[o] for o in selected_options]
            else:
                if selected_option not in available_options.keys():
                    self.stderr.write("The provided value is not a valid option.")
                else:
                    return available_options[selected_option]

    def create_booking(self):

        # Products

        available_products = self.client.get_available_products()

        if not available_products:
            self.stderr.write("No products found.")
            return

        selected_products = self._show_options(
            available_products, lambda x: x.name, "product", allow_multi=True
        )

        # Locations

        available_locations = self.client.get_locations(selected_products)

        selected_location = self._show_options(
            available_locations, lambda x: x.name, "location"
        )

        # Dates

        available_dates = self.client.get_dates(selected_products, selected_location)

        selected_date = self._show_options(
            available_dates, lambda x: x.strftime(DATE_PARSE_FORMAT), "date"
        )

        # Times

        available_times = self.client.get_times(
            selected_products, selected_location, selected_date
        )

        selected_datetime = self._show_options(
            available_times, lambda x: x.strftime(TIME_PARSE_FORMAT), "time"
        )

        # Customer

        customer = AppointmentClient(last_name="Doe", birthdate=date(1970, 1, 1))

        # Book

        booking_id = None

        self.stdout.write(
            "Concept appointment\n"
            + f"Product(s)   : {', '.join([p.name for p in selected_products])}\n"
            + f"Location     : {selected_location.name}\n"
            + f"Date and time: {selected_datetime}"
        )
        while True:
            do_book = input("Do you want to book this appointment [y/n]: ")
            if do_book == "y":
                try:
                    booking_id = self.client.create_appointment(
                        selected_products,
                        selected_location,
                        selected_datetime,
                        customer,
                        remarks="This is a test!",
                    )
                    self.stdout.write(f"Appointment created with ID: {booking_id}")
                except Exception as exc:
                    self.stderr.write(f"Failed to create appointment: {exc}")
                break
            elif do_book == "n":
                self.stdout.write("Appointment was not booked.")
                return
            else:
                self.stderr.write(f"{do_book} is not a valid choice.")

    def show_booking(self, booking_id=None):

        while not booking_id:
            booking_id = input("Appointment ID: ")

        self.stdout.write("Appointment details (retrieved):")
        try:
            details = self.client.get_appointment_details(booking_id)
        except Exception as exc:
            self.stderr.write(f"Failed to get appointment details: {exc}")
            return

        for k in details.__annotations__.keys():
            self.stdout.write(f"- {k}: {getattr(details, k)}")

    def cancel_booking(self, booking_id=None):

        while not booking_id:
            booking_id = input("Appointment ID: ")

        self.show_booking(booking_id)

        while True:
            do_cancel = input("Do you want to cancel this appointment [y/n]? ")
            if do_cancel == "y":
                try:
                    self.client.delete_appointment(booking_id)
                    self.stdout.write(f"Appointment cancelled succesfully.")
                except Exception as exc:
                    self.stderr.write(f"Failed to cancel appointment: {exc}")
                break
            elif do_cancel == "n":
                self.stdout.write("Appointment was not cancelled.")
            else:
                self.stderr.write(f"{do_cancel} is not a valid choice.")

    def exit(self):
        pass
