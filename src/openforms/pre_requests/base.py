from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .clients import PreRequestClientContext


@dataclass
class PreRequestHookBase(ABC):
    identifier: str

    @abstractmethod
    def __call__(
        self,
        method: str,
        url: str,
        kwargs: dict,
        context: Optional[PreRequestClientContext] = None,
    ) -> None:
        raise NotImplementedError()  # pragma: nocover
