from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from .renderer import Renderer  # pragma: nocover


@dataclass
class Node(ABC):
    """
    Abstract node base class.

    All specific render node types must inherit from this class. Nodes must be able
    to yield their children. Nodes are specialized to handle the data they are given.
    """

    renderer: "Renderer"

    @property
    def mode(self) -> str:
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

    @abstractmethod
    def get_children(self) -> Iterator["Node"]:  # pragma: nocover
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
    def render(self) -> str:  # pragma: nocover
        """
        Output the result of rendering the particular type of node.
        """
        ...
