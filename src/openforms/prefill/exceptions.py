class PrefillSkipped(Exception):
    """
    Indicate that the prefill plugin decided to skip the prefill.

    Raise this exception in a plugin if the preconditions or business logic lead to the
    prefill not being necessary, e.g. a certain authentication attribute is not available
    or configuration of the plugin results in no operation needing to be performed. If
    the implementation decides to not make any external calls to perform the prefill,
    then you should raise this exception.

    Do not raise this exception in case of prefill failure - those errors are handled
    separately.
    """

    pass
