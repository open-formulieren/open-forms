import logging


LOGGING_LEVEL = {'0': logging.ERROR, '1': logging.WARNING, '2': logging.DEBUG, '3': logging.DEBUG}


def create_handler(verbosity, message='%(message)s'):
    """
    Create a handler which can output logged messages to the console (the log
    level output depends on the verbosity level).
    """
    handler = logging.StreamHandler()
    handler.setLevel(LOGGING_LEVEL[str(verbosity)])
    formatter = logging.Formatter(message)
    handler.setFormatter(formatter)
    return handler
