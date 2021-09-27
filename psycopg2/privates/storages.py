from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.functional import LazyObject, cached_property


class PrivateMediaFileSystemStorage(FileSystemStorage):
    """
    Storage that puts files in the private media folder that isn't
    globally available.
    """

    def _clear_cached_properties(self, setting, **kwargs):
        super()._clear_cached_properties(setting, **kwargs)
        if setting == "PRIVATE_MEDIA_ROOT":
            self.__dict__.pop("base_location", None)
            self.__dict__.pop("location", None)
        elif setting == "PRIVATE_MEDIA_URL":
            self.__dict__.pop("base_url", None)

    @cached_property
    def base_location(self):
        return self._value_or_setting(self._location, settings.PRIVATE_MEDIA_ROOT)

    @cached_property
    def base_url(self):
        if self._base_url is not None and not self._base_url.endswith("/"):
            self._base_url += "/"
        return self._value_or_setting(self._base_url, settings.PRIVATE_MEDIA_URL)


class PrivateMediaStorage(LazyObject):
    def _setup(self):
        self._wrapped = PrivateMediaFileSystemStorage()


private_media_storage = PrivateMediaStorage()
