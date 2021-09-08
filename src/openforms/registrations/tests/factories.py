from dataclasses import dataclass

import factory


@dataclass
class ReferenceHolder:
    reference: str


class ReferenceHolderFactory(factory.Factory):
    reference = factory.Sequence(lambda n: f"reference-{n}")

    class Meta:
        model = ReferenceHolder
