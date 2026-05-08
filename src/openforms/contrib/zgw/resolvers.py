from collections.abc import MutableMapping
from datetime import date
from typing import TypedDict

from .clients import CatalogiClient
from .clients.catalogi import Catalogus, InformatieObjectType


class CatalogueParams(TypedDict):
    domain: str
    rsin: str


# domain, RSIN
type CatalogueIdentifiers = tuple[str, str]

# catalogue url, description, valid on
type DocumentTypeIdentifiers = tuple[str, str, date]


class DocumentTypeResolver:
    """
    Resolver helper that caches lookups to prevent identical network requests.

    Resolver instances are intended to be short-lived (e.g. the duration of an HTTP
    request-response cycle or celery task), so that the garbage collector cleans up the
    internal in-memory cache.
    """

    def __init__(self, client: CatalogiClient):
        self.client = client
        self._catalogue_cache: MutableMapping[
            CatalogueIdentifiers, Catalogus | None
        ] = {}
        self._document_type_cache: MutableMapping[
            DocumentTypeIdentifiers, InformatieObjectType | None
        ] = {}

    def resolve(
        self,
        *,
        catalogue: CatalogueParams,
        description: str,
        on_date: date,
        within_casetype: str = "",
    ) -> InformatieObjectType:
        """
        Resolve a document type versio within a catalogue at a particular date.
        """
        catalogus = self._resolve_catalogue(catalogue)
        if catalogus is None:
            raise RuntimeError(f"Could not resolve catalogue {catalogue}")

        cache_key: DocumentTypeIdentifiers = (catalogus["url"], description, on_date)
        if cache_key not in self._document_type_cache:
            versions = self.client.find_informatieobjecttypen(
                catalogus=catalogus["url"],
                description=description,
                valid_on=on_date,
                within_casetype=within_casetype,
            )
            self._document_type_cache[cache_key] = (
                None if versions is None else versions[0]
            )

        version = self._document_type_cache[cache_key]
        if version is None:
            raise RuntimeError(
                "Could not find a document type with description "
                f"'{description}' in the case type that is valid on "
                f"{on_date.isoformat()}."
            )
        return version

    # TODO: when expanding this to the zaaktypen, this can be extracted into a separate
    # resolver class
    def _resolve_catalogue(self, catalogue: CatalogueParams) -> Catalogus | None:
        cache_key: CatalogueIdentifiers = (catalogue["domain"], catalogue["rsin"])
        if cache_key not in self._catalogue_cache:
            self._catalogue_cache[cache_key] = self.client.find_catalogus(**catalogue)
        return self._catalogue_cache[cache_key]
