"""
Wrap around concurrent.futures to add Django-specific cleanup behaviour.
"""
import functools
import logging
import threading
from concurrent import futures

from django.db import close_old_connections

logger = logging.getLogger(__name__)


def wrap_fn(fn):
    """
    Closes the database connections when the original function has completed.
    """

    @functools.wraps(fn)
    def wrapped(*fn_args, **fn_kwargs):
        try:
            return fn(*fn_args, **fn_kwargs)
        finally:
            logger.debug(
                "Closing all database connections",
                extra={"thread_id": threading.get_ident()},
            )
            close_old_connections()

    return wrapped


class parallel:
    def __init__(self, **kwargs):
        self.executor = futures.ThreadPoolExecutor(**kwargs)

    def submit(*args, **kwargs):
        if len(args) >= 2:
            self, _fn, *args = args
        elif "fn" in kwargs:
            _fn = kwargs.pop("fn")
            self, *args = args

        fn = wrap_fn(_fn)

        return self.executor.submit(fn, *args, **kwargs)

    def map(self, fn, *iterables, timeout=None, chunksize=1):
        return self.executor.map(
            wrap_fn(fn), *iterables, timeout=timeout, chunksize=chunksize
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.executor.__exit__(exc_type, exc_val, exc_tb)
