from typing import Protocol, Sequence, TypeVar


class HasAge(Protocol):
    @property
    def age(self) -> int | None: ...


T = TypeVar("T", bound=HasAge)


def filter_members_by_age(
    results: Sequence[T],
    min_age: int | None = None,
    max_age: int | None = None,
) -> list[T]:
    min_age = min_age or 0
    max_age = max_age or 500

    return [
        member
        for member in results
        if member.age is not None and min_age <= member.age <= max_age
    ]
