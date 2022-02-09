from typing import List

from django.db import models
from django.db.models.base import ModelBase


def get_file_field_names(model: ModelBase) -> List[str]:
    """
    Collect the model field names that are (subclasses) of models.FileField.
    """
    all_fields = model._meta.get_fields()
    file_fields = [field for field in all_fields if isinstance(field, models.FileField)]
    return [field.name for field in file_fields]
