"""
Implement :class:`django.db.models.FileField` related utilities.

These utilities apply to file fields and subclasses thereof.
"""
from typing import List

from django.db import models
from django.db.models.base import ModelBase


def get_file_field_names(model: ModelBase) -> List[str]:
    """
    Collect names of :class:`django.db.models.FileField` (& subclass) model fields.
    """
    all_fields = model._meta.get_fields()
    file_fields = [field for field in all_fields if isinstance(field, models.FileField)]
    return [field.name for field in file_fields]


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
        for name in file_field_names:
            filefield = getattr(self, name)
            filefield.delete(save=False)
        return super().delete(*args, **kwargs)

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

    def _delete_filefields_storage(self) -> None:
        # TODO: we might want to wrap this in transaction.on_commit, see also
        # DeleteFileFieldFilesMixin
        file_field_names = get_file_field_names(self.model)
        del_query = self._chain()

        # iterator in case we're dealing with large querysets and memory could be
        # exhausted
        for obj in del_query.iterator():
            for name in file_field_names:
                filefield = getattr(obj, name)
                filefield.delete(save=False)

    def _raw_delete(self, using):
        # raw delete is called in fast_deletes
        self._delete_filefields_storage()
        return super()._raw_delete(using)

    _raw_delete.alters_data = True

    def delete(self):
        self._delete_filefields_storage()
        return super().delete()

    delete.alters_data = True
    delete.queryset_only = True
