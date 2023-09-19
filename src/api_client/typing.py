from typing import Any, Protocol


class APIClientFactory(Protocol):
    def get_client_base_url(self) -> str:  # pragma: no cover
        """
        Return the API root/base URL to which relative URLs are made.
        """
        ...

    def get_client_session_kwargs(self) -> dict[str, Any]:  # pragma: no cover
        """
        Return kwargs to feed to :class:`requests.Session` when using the client.

        Provide a dict of possible :class:`requests.Session` attributes which will
        (typically) be used as defaults for each request sent from the session, such as
        ``auth`` for authentication or ``cert`` and/or ``verify`` for mutual TLS
        purposes. Other examples would be a ``timeout`` that's service-specific (and
        potentially different from the global default).

        Note that many of these kwargs can still be overridden at call time, e.g.:

        .. code-block:: python

            with APIClient.configure_from(some_service) as client:
                response = client.get("some/relative/path", timeout=10)
        """
        ...
