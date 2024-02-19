from dataclasses import dataclass
from typing import Protocol


class DMNInputParameter(Protocol):
    expression: str
    label: str


class DMNOutputParameter(Protocol):
    name: str
    label: str


class DMNInputOutput(Protocol):
    inputs: list[DMNInputParameter]
    outputs: list[DMNOutputParameter]


@dataclass
class GenericInputOutput:
    inputs: list[DMNInputParameter]
    outputs: list[DMNOutputParameter]
