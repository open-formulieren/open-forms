from dataclasses import dataclass
from typing import List, Optional, Tuple

from django.contrib.admin.templatetags.admin_list import _boolean_icon


@dataclass
class Entry:
    name: str
    status: Optional[bool] = None
    actions: Optional[List[Tuple[str, str]]] = None
    error: str = ""

    @property
    def status_icon(self):
        return _boolean_icon(self.status)
