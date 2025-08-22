import itertools
from collections.abc import Collection

from opentelemetry.metrics import Observation


class MetricsAssertMixin:
    def assertMarkedGlobal(self, result: Collection[Observation]) -> None:
        self.assertTrue(  # pyright: ignore[reportAttributeAccessIssue]
            all(
                observation.attributes and observation.attributes["scope"] == "global"
                for observation in result
            ),
            "Global metrics must be labelled as such",
        )

    @staticmethod
    def _group_observations_by(
        observations: Collection[Observation], attribute: str
    ) -> dict[str, int | float]:
        def _key_func(o: Observation) -> str:
            assert o.attributes is not None
            form_name = o.attributes[attribute]
            assert isinstance(form_name, str)
            return form_name

        grouped_by_attribute = itertools.groupby(
            sorted(observations, key=_key_func), key=_key_func
        )
        return {
            form_name: sum(o.value for o in _observations)
            for form_name, _observations in grouped_by_attribute
        }
