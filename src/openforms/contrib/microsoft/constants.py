from django.db import models


class ConflictHandling(models.TextChoices):
    fail = "fail"
    replace = "replace"
    rename = "rename"
