from ..setup import setup_env

setup_env()

from .app import app  # noqa: E402

__all__ = ("app",)
