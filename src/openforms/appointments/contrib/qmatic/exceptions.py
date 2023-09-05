from ...exceptions import AppointmentException


class QmaticException(AppointmentException):
    pass


class GracefulQmaticException(QmaticException):
    """
    Raise when the program execution can continue with a fallback error.
    """
