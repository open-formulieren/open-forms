"""
Manage OpenAPI Specification 3.0.x schemas.
"""
import requests
import yaml

__all__ = ["schema_fetcher"]


class SchemaFetcher:
    """
    Retrieve and cache OpenAPI Specification schemas

    Caching is done based on the URL of the schema. The schema is parsed from
    YAML and the resulting dictionary is returned/stored.
    """

    def __init__(self):
        self.cache = {}

    def fetch(self, url: str, *args, **kwargs) -> dict:
        """
        Fetch a YAML-based OAS 3.0.x schema.

        Any extra arguments or keyword arguments are forwarded to
        :func:`requests.get`.

        :param url: The URL to the schema, must point to a YAML object
        :raises: :class:`requests.RequestException` if the URL doesn't properly
          resolve
        :raises: :class:`ValueError` if the API-spec is not a OAS 3.0.x spec
        """
        if url in self.cache:
            return self.cache[url]

        response = requests.get(url, *args, **kwargs)
        response.raise_for_status()

        spec = yaml.safe_load(response.content)
        spec_version = response.headers.get(
            "X-OAS-Version", spec.get("openapi", spec.get("swagger", ""))
        )
        if not spec_version.startswith("3.0"):
            raise ValueError("Unsupported spec version: {}".format(spec_version))

        self.cache[url] = spec

        return spec


# sentinel instance, with a cache
schema_fetcher = SchemaFetcher()
"""
Sentinel schema fetcher instance, used by :class:`zds_client.client.Client`.

Note that you can mutate ``schema_fetcher.cache`` to replace it with another cache
backend, for example.
"""
