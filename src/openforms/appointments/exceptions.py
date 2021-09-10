class AppointmentException(Exception):
    pass


class AppointmentDeleteFailed(AppointmentException):
    pass


class AppointmentCreateFailed(AppointmentException):
    pass


class AppointmentInteractionFailed(AppointmentException):
    def __init__(self, *args, **kwargs):
        self.should_retry = kwargs.pop("should_retry", False)
        super().__init__(*args, **kwargs)


class AppointmentRegistrationFailed(AppointmentInteractionFailed):
    pass


class AppointmentUpdateFailed(AppointmentInteractionFailed):
    pass
