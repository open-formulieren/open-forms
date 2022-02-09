from openforms.utils.files import get_file_field_names


class DeleteFileFieldFilesMixin:
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
