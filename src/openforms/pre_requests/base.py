from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from openforms.plugins.plugin import AbstractBasePlugin

if TYPE_CHECKING:
    from .clients import PreRequestClientContext


@dataclass
class PreRequestHookBase(ABC, AbstractBasePlugin):
    identifier: str

    @abstractmethod
    def __call__(
        self,
        method: str,
        url: str,
        kwargs: dict | None,
        context: PreRequestClientContext | None = None,
    ) -> None:
        raise NotImplementedError()
