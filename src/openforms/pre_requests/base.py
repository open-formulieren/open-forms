from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from openforms.plugins.plugin import AbstractBasePlugin

if TYPE_CHECKING:
    from .clients import PreRequestClientContext


class PreRequestHookBase(ABC, AbstractBasePlugin):
    @abstractmethod
    def __call__(
        self,
        method: str,
        url: str,
        kwargs: dict | None,
        context: PreRequestClientContext | None = None,
    ) -> None:
        raise NotImplementedError()
