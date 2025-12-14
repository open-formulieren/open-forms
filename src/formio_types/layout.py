from __future__ import annotations

from ._base import Component


class Content(Component, tag="content"):
    html: str
