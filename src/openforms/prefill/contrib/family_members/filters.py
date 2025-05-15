from collections.abc import Sequence
from typing import Protocol


class HasAge(Protocol):
    @property
    def age(self) -> int | None: ...


def filter_members_by_age[T: HasAge](
    results: Sequence[T],
    min_age: int | None = None,
    max_age: int | None = None,
) -> Sequence[T]:
    # skip filters if nothing is requested
    if min_age is None and max_age is None:
        return results

    min_age = min_age or 0
    max_age = max_age or 500

    return [
        member
        for member in results
        if member.age is not None and min_age <= member.age <= max_age
    ]
