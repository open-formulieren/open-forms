"""
Implement :class:`django.db.models.FileField` related utilities.

These utilities apply to file fields and subclasses thereof.
"""

from contextlib import contextmanager

from django.db import models, transaction
from django.db.models import Model
from django.db.models.fields.files import FieldFile

import sentry_sdk
import structlog

logger = structlog.stdlib.get_logger(__name__)


def get_file_field_names(model: type[Model]) -> list[str]:
    """
    Collect names of :class:`django.db.models.FileField` (& subclass) model fields.
    """
    all_fields = model._meta.get_fields()
    file_fields = [field for field in all_fields if isinstance(field, models.FileField)]
    return [field.name for field in file_fields]


@contextmanager
def log_deletes(filefield: FieldFile):
    """
    Context manager adding robustness to model file field deletes.

    Deletes that fail for whatever reason are logged with ``level`` and exceptions
    are supressed.
    """
    instance = filefield.instance
    with structlog.contextvars.bound_contextvars(
        model=type(instance),
        pk=instance.pk,
        field=filefield.field.name,
        path=filefield.path,
    ):
        try:
            yield
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            logger.warning("file_delete_failure", exc_info=exc)
        else:
            logger.debug("file_deleted")


def _delete_obj_files(fields: list[str], obj: models.Model) -> None:
    for name in fields:
        filefield = getattr(obj, name)
        with log_deletes(filefield):
            filefield.delete(save=False)


class DeleteFileFieldFilesMixin:
    """
    Model mixin ensuring file deletion on database record deletion.

    All file fields as part of the model will have the content removed as part of
    the instance deletion.
    """

    def delete(self, *args, **kwargs):
        # maybe the file deletion should be in a transaction.on_commit handler,
        # in case the DB deletion errors but then the file is gone?
        # Postponing that decision, as likely a number of tests will fail because they
        # run in transactions.
        file_field_names = get_file_field_names(type(self))
        with transaction.atomic():
            result = super().delete(*args, **kwargs)
            transaction.on_commit(lambda: _delete_obj_files(file_field_names, self))
        return result

    delete.alters_data = True


class DeleteFilesQuerySetMixin:
    """
    Delete files on :meth:`django.db.models.QuerySet.delete` calls.

    All file fields as part of the model will have the content removed as part of
    the deletion of every instance in the queryset.

    .. note:: For cascading deletes with related objects, you should specify
       ``model.Meta.base_manager_name`` on the related model(s), otherwise Django
       doesn't use your custom queryset class.
    """

    def _get_delete_filefields_storage_callback(self) -> callable:
        file_field_names = get_file_field_names(self.model)

        # we cannot use an iterator, as the query will come up empty after the DELETE
        # query is done. This could potentially lead to memory exhaustion on large
        # datasets
        objects_to_delete = list(self._chain())

        def callback():
            for obj in objects_to_delete:
                _delete_obj_files(file_field_names, obj)

        return callback

    def _raw_delete(self, using):
        # raw delete is called in fast_deletes
        callback = self._get_delete_filefields_storage_callback()
        with transaction.atomic():
            result = super()._raw_delete(using)
            transaction.on_commit(callback)
        return result

    _raw_delete.alters_data = True

    def delete(self):
        callback = self._get_delete_filefields_storage_callback()
        with transaction.atomic():
            result = super().delete()
            transaction.on_commit(callback)
        return result

    delete.alters_data = True
    delete.queryset_only = True
