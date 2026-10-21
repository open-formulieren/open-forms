from collections.abc import MutableMapping
from uuid import UUID


class UUIDMap:
    """
    Helper class to keep track of UUID's that have been changed during import and update
    the import data accordingly.
    """

    def __init__(self):
        self.mapping: MutableMapping[str, str] = {}
        """
        Mapping of old UUID's to new UUID's.
        """

    def apply_to_data(self, data: str) -> str:
        """
        Replace all old UUID's for their new counterpart in the data, and return the
        updated data.
        """
        for old, new in self.mapping.items():
            data = data.replace(old, new)
        return data

    def add(self, old_uuid: str | None, new_uuid: str | UUID | None) -> None:
        """
        Add the old and new UUID's to the mapping.
        """
        if old_uuid and new_uuid:
            self.mapping[old_uuid] = str(new_uuid)
