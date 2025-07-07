from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .constants import RenderModes

if TYPE_CHECKING:
    from .renderer import Renderer


@dataclass
class Node(ABC):
    """
    Abstract node base class.

    All specific render node types must inherit from this class. Nodes must be able
    to yield their children. Nodes are specialized to handle the data they are given.
    """

    renderer: "Renderer"

    @property
    def mode(self) -> RenderModes:
        return self.renderer.mode

    @property
    def as_html(self) -> bool:
        return self.renderer.as_html

    @property
    def is_visible(self) -> bool:  # pragma: nocover
        """
        Determine if the node is visible for the given render mode and context.
        """
        return True

    @property
    def has_children(self) -> bool:
        generator = self.get_children()
        try:
            next(generator)
        except StopIteration:
            return False
        else:
            return True

    @abstractmethod
    def get_children(self) -> Iterator["Node"]:
        """
        Yield the specific child nodes in the node tree.
        """
        raise NotImplementedError("You must implement the 'get_children' method.")

    def __iter__(self) -> Iterator["Node"]:
        """
        Yield the child nodes.
        """
        yield from self.get_children()

    @abstractmethod
    def render(self) -> str:
        """
        Output the result of rendering the particular type of node.
        """
        ...
