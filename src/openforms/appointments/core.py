"""
Core implementation of the generic API.

This module is the follow-up to the bulk of functionality in utils.py, which is doing
way too much but can't be easily refactored without breaking existing functionality.
"""
from .base import BasePlugin, CustomerDetails, Location, Product
from .models import Appointment
from .registry import register

__all__ = ["book"]


def book(appointment: Appointment, remarks: str = "") -> str:
    """
    Book the appointment from the data in the model instance.
    """
    plugin = register[appointment.plugin]
    assert isinstance(plugin, BasePlugin)

    # convert DB data into domain objects
    products = [
        Product(identifier=ap.product_id, amount=ap.amount, name="")
        for ap in appointment.products.all()
    ]
    location = Location(identifier=appointment.location, name="")
    customer = CustomerDetails(details=appointment.contact_details)

    result = plugin.create_appointment(
        products,
        location,
        appointment.datetime,
        customer,
        remarks=remarks,
    )
    return result
