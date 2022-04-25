from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .renderer import Renderer

NODE_TYPES = {}


@dataclass
class Node(ABC):
    """
    Abstract node base class.

    All specific render node types must inherit from this class.
    """

    renderer: "Renderer"

    def __init_subclass__(cls, **kwargs):
        # register subclasses as node types so we can pass this to django template
        # rendering context
        NODE_TYPES[cls.__name__] = cls

    @property
    def type(self) -> str:
        """
        Name of the node type
        """
        return type(self).__name__

    @property
    def mode(self) -> str:
        return self.renderer.mode

    @property
    def as_html(self) -> bool:
        return self.renderer.as_html

    @abstractmethod
    def render(self) -> str:
        """
        Output the result of rendering the particular type of node given a context.
        """
        ...
