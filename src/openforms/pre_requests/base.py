from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


@dataclass
class PreRequestHookBase(ABC):
    identifier: str

    @abstractmethod
    def __call__(
        self, submission: "Submission", method: str, url: str, kwargs: dict
    ) -> None:
        raise NotImplementedError()  # pragma: nocover
