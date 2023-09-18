# API Client

Implements a generic/base API client as a wrapper around `requests` API.

The client is a general purpose HTTP client, meaning it's not limited to RESTful services but also
suitable for SOAP (for example).

## Design constraints

- Must support the `requests.Session` API
- Must be compatible with `zgw_consumers.Service`, `stuf.StUFService` and `soap.SOAPService`
- Should encourage best practices (closing resources after use)
- Should not create problems when used with other libraries, e.g. `requests-oath2client`

The client is "simply" a subclass of `requests.Session` which allows us to achieve many of the above
constraints.

Eventually we'd like to jump ship to use `httpx` rather than `requests` - it has a similar API, but
it's also `async` / `await` capable. The abstraction of the underlying driver (now requests, later
httpx) should not matter and most importantly, not be leaky.

## Usage

TODO
