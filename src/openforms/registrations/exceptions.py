class RegistrationFailed(Exception):
    def __init__(self, *args, **kwargs):
        self.response = kwargs.pop("response", None)
        super().__init__(*args, **kwargs)


class NoSubmissionReference(Exception):
    pass
