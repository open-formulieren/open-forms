from abc import ABC
from dataclasses import dataclass
from typing import Literal, TypeAlias, Union

# Naming is based on
# https://en.wikipedia.org/wiki/Hindley%E2%80%93Milner_type_system


class Expression(ABC):
    "e"
    pass


@dataclass
class NumberLiteral(Expression):
    value: int | float


@dataclass
class StringLiteral(Expression):
    value: str


@dataclass
class Variable(Expression):
    "x"
    x: str


@dataclass
class Application(Expression):
    "e1 e2"
    e1: Expression
    e2: Expression


@dataclass
class Abstraction(Expression):
    "λx.e"
    x: str
    e: Expression


@dataclass
class Let(Expression):
    "let x = e1 in e2"
    x: str
    e1: Expression
    e2: Expression


# τ, tau or Type
MonoType: TypeAlias = Union["TypeApplication", "TypeVariable"]
# σ, sigma or TypeScheme
PolyType: TypeAlias = Union["TypeQuantifier", MonoType]


@dataclass
class TypeVariable:
    "α    alpha"
    alpha: str

    def __contains__(self, a: "TypeVariable"):
        return self.alpha == a.alpha

    def __str__(self):
        return self.alpha


TypeFunction = Literal[
    "->",  # function
    "[]",  # array
    "Either",  # Union type to support return type polymorphism
    # Primitives
    "Bool",  # "true" / "false"
    "Null",  # "null" aka None aka unit aka ()
    "Number",  # number
    "String",  # string
]


@dataclass
class TypeApplication:
    "Cτ...τ"
    C: TypeFunction
    taus: tuple[()] | tuple[MonoType] | tuple[MonoType, MonoType] = ()

    def __contains__(self, a: TypeVariable):
        return any(a in t for t in self.taus)

    def __post_init__(self):
        match self:
            case TypeApplication("Either", (a, b)) if a == b:
                # simplify Either a a to a
                if isinstance(a, TypeApplication):
                    self.C = a.C
                    self.taus = a.taus

    def __str__(self) -> str:
        match self.C, [str(t) for t in self.taus]:
            case C, []:
                return C
            case "->", taus:
                return " -> ".join(taus)
            case "[]", [t]:
                return f"[{t}]"
            case _:
                return f"{self.C} {' '.join(map(str, self.taus))}"

    def __repr__(self) -> str:
        return str(self)


@dataclass
class TypeQuantifier:
    "∀α.σ    forall alpha . sigma"
    alpha: str
    sigma: MonoType | PolyType
    # TODO sigma is actually a chain of TypeQantifiers that end in a MonoType
    # As in the Folkore paper they write a vector α with an arrow over the alpha
    # so maybe this makes more sense:
    # alphas: Sequence[str]
    # sigma: MonoType

    def __str__(self):
        return f"∀{self.alpha}.{self.sigma}"

    def __repr__(self) -> str:
        return str(self)


class Context(dict[str, PolyType]):
    pass
