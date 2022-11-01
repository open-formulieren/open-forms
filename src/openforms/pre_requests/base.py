from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PreRequestHookBase(ABC):
    identifier: str

    @abstractmethod
    def __call__(self, method: str, url: str, kwargs: dict) -> None:
        raise NotImplementedError()  # pragma: nocover
