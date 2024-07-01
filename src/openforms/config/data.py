from dataclasses import dataclass
from typing import TypeAlias

from django.contrib.admin.templatetags.admin_list import _boolean_icon

from openforms.typing import StrOrPromise

Action: TypeAlias = tuple[StrOrPromise, str]  # (label, reversed URL path)


@dataclass
class Entry:
    name: str
    status: bool | None = None
    actions: list[Action] | None = None
    error: str = ""

    @property
    def status_icon(self):
        return _boolean_icon(self.status)
