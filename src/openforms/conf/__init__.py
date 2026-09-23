import importlib.util

# time_machine is a dev/testing dependency
if importlib.util.find_spec("time_machine") is not None:
    import time_machine

    time_machine.naive_mode = time_machine.NaiveMode.LOCAL
else:  # pragma: no cover
    pass
