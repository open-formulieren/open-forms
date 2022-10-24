from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PreRequestHookBase(ABC):
    identifier: str

    @abstractmethod
    def __call__(self, method: str, url: str, **kwargs) -> Any:
        raise NotImplementedError()  # pragma: nocover
