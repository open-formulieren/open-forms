from ...exceptions import AppointmentException


class JCCError(AppointmentException):
    pass


class GracefulJCCError(JCCError):
    """
    Raise when the program execution can continue with a fallback error.
    """
