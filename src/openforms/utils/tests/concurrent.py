from concurrent.futures import Executor, Future
from contextlib import contextmanager
from unittest.mock import patch


class _DummyThreadPoolExecutor(Executor):
    def __init__(self, max_workers=None):
        self._max_workers = max_workers

    def submit(self, fn, *args, **kwargs):
        future = Future()
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            future.set_exception(exc)
        else:
            future.set_result(result)
        return future


@contextmanager
def mock_parallel_executor():
    """
    Mock the zgw_consumers.concurrent.parallel helper to not use real threads.

    Useful for tests where queries are done in the tasks submitted to the pool - these
    changes cannot be rolled back since the test DB transaction is not aware of the
    extra DB transactions in the tests. This in turn leads to broken test isolation.
    """
    executor_patcher = patch(
        "zgw_consumers.concurrent.futures.ThreadPoolExecutor",
        new=_DummyThreadPoolExecutor,
    )
    conn_patcher = patch(
        "zgw_consumers.concurrent.close_db_connections", return_value=None
    )
    with executor_patcher, conn_patcher:
        yield
