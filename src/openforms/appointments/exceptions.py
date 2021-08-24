class AppointmentException(Exception):
    pass


class AppointmentDeleteFailed(AppointmentException):
    pass


class AppointmentCreateFailed(AppointmentException):
    pass
