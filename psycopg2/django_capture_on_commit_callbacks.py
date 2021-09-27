from contextlib import contextmanager

from django.db import DEFAULT_DB_ALIAS, connections


@contextmanager
def capture_on_commit_callbacks(*, using=DEFAULT_DB_ALIAS, execute=False):
    callbacks = []
    start_count = len(connections[using].run_on_commit)
    try:
        yield callbacks
    finally:
        run_on_commit = connections[using].run_on_commit[start_count:]
        callbacks[:] = [func for sids, func in run_on_commit]
        if execute:
            for callback in callbacks:
                callback()


class TestCaseMixin:
    @classmethod
    def captureOnCommitCallbacks(cls, *, using=DEFAULT_DB_ALIAS, execute=False):
        return capture_on_commit_callbacks(using=using, execute=execute)
