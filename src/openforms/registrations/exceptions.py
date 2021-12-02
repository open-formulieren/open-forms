class RegistrationFailed(Exception):
    def __init__(self, *args, **kwargs):
        self.response = kwargs.pop("response", None)


class NoSubmissionReference(Exception):
    pass
