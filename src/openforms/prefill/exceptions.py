class PrefillSkippedException(Exception):
    """
    Custom exception for prefill plugins

    This is used in cases where the plugin, for some reason, doesn't manage to complete
    the operation. This is happening before even making an external call, which can cause
    another Exception.
    """

    pass
