from typing import TYPE_CHECKING, Any, Optional, TypedDict

from zgw_consumers.client import ZGWClient

from .registry import register as registry

if TYPE_CHECKING:
    from openforms.submissions.models import Submission


class PreRequestClientContext(TypedDict):
    submission: Optional["Submission"]


class PreRequestZGWClient(ZGWClient):
    _context = None

    def pre_request(
        self, method: str, url: str, kwargs: Optional[dict] = None
    ) -> Any:
        result = super().pre_request(method, url, kwargs)

        if not self._context or not (submission := self._context.get("submission")):
            return result

        for pre_request in registry:
            pre_request(submission, method, url, kwargs)

        return result

    @property
    def context(self) -> PreRequestClientContext:
        return self._context

    @context.setter
    def context(self, context: PreRequestClientContext) -> None:
        self._context = context
