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
