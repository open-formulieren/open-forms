from urllib.parse import urlsplit, urlunsplit

from django.db import models
from django.db.models.functions import Length

from zds_client import Client


class ServiceManager(models.Manager):
    def get_client_for(self, url: str) -> Client:
        """
        Return a Client instance capable of fetching the url.

        The URL is supposed to represent a resource in the API. Based on the URL, the
        service object is returned that can be used to fetch the object.
        """
        split_url = urlsplit(url)
        scheme_and_domain = urlunsplit(split_url[:2] + ("", "", ""))

        candidates = (
            self.filter(api_root__startswith=scheme_and_domain)
            .annotate(api_root_length=Length("api_root"))
            .order_by("-api_root_length")
        )

        # select the one matching
        for candidate in candidates.iterator():
            if url.startswith(candidate.api_root):
                service = candidate
                break
        else:
            raise self.model.DoesNotExist(f"No service found for url '{url}'")

        return service.build_client()
