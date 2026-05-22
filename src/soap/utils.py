import tempfile

from django.core.files.storage import FileSystemStorage, InMemoryStorage
from django.db.models.fields.files import FieldFile


def ensure_file_exists_on_disk(field: FieldFile) -> str:
    # Copied from django-digid-eherkenning
    match field.storage:
        case FileSystemStorage():  # pragma: no cover
            return field.path
        case InMemoryStorage():
            # TODO: figure out a solution to get these files/directories cleaned up once
            # tests complete. Maybe setting up a signal dispatch?
            tmp_input_file = tempfile.NamedTemporaryFile(mode="wb", delete=False)
            field.open("rb")
            field.seek(0)
            for chunk in field.chunks():
                tmp_input_file.write(chunk)
            tmp_input_file.flush()
            return tmp_input_file.name
        case _:  # pragma: no cover
            raise NotImplementedError()
