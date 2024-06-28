class InvalidPluginConfiguration(Exception):
    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)


class PluginNotEnabled(Exception):
    pass
