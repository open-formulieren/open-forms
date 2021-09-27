"""
Support downstream APIs using django-rest-framework.

This package includes support for API's using API models. In this way, the API acts
as a gateway API, consuming services defined by zgw-consumers, and
re-formatting/serializing the data back into the downstream API responses. A typical
set-up would be a Single-Page-App having its own dedicated gateway API, which fetches
data from other services so that the SPA only has one backend to consider.
"""
