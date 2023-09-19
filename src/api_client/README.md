# API Client

Implements a generic/base API client as a wrapper around `requests` API.

The client is a general purpose HTTP client, meaning it's not limited to RESTful services but also
suitable for SOAP (for example).

## Usage

The client is a thin wrapper around `requests.Session`, with some guard rails in place:

- specify a base URL and check that absolute URL requests fit within the base URL
- manage resources by closing the session even for one-off requests

There are two ways to instantiate a client.

- from a factory (preferred)
- manually

The factory approach is preferred as it provides the most robust way to honour authentication
configuration such as credentials and mutual TLS parameters.

### From a factory

Factories must implement the `api_client.typing.APIClientFactory` protocol, which provides the
client instance with the base URL and any session-level keyword arguments. This could come from a
Django model instance, or some class taking a YAML configuration file.

```py
from api_client import APIClient

from .factories import my_factory

client = APIClient.configure_from(my_factory)

with client:
    # ⚡️ context manager -> uses connection pooling and is recommended!
    response1 = client.get("some-relative-path", params={"foo": ["bar"]})
    response2 = client.post("other-path", json={...})
```

### Manually

```py
from api_client import APIClient
from requests.auth import

client = APIClient(
    "https://example.com/api/v1/",
    auth=HTTPBasicAuth("superuser", "letmein"),
    verify="/path/to/custom/ca-bundle.pem",
)

with client:
    # ⚡️ context manager -> uses connection pooling and is recommended!
    response1 = client.get("some-relative-path", params={"foo": ["bar"]})
    response2 = client.post("other-path", json={...})
```

## Design constraints

- Must support the `requests.Session` API
- Must be compatible with `zgw_consumers.Service`, `stuf.StUFService` and `soap.SOAPService`
- Should encourage best practices (closing resources after use)
- Should not create problems when used with other libraries, e.g. `requests-oauth2client`

The client is "simply" a subclass of `requests.Session` which allows us to achieve many of the above
constraints.

Eventually we'd like to jump ship to use `httpx` rather than `requests` - it has a similar API, but
it's also `async` / `await` capable. The abstraction of the underlying driver (now requests, later
httpx) should not matter and most importantly, not be leaky.

NOTE: not being leaky here means that you can use the requests API (in the future: httpx) like you
would normally do without this library getting in the way.
