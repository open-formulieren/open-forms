from ...exceptions import AppointmentException


class JccRestException(AppointmentException):
    pass


class GracefulJccRestException(JccRestException):
    """
    Raise when the program execution can continue with a fallback error.
    """
