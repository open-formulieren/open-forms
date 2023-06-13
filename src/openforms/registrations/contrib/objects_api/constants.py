from django.db import models


class JsonTemplateValidatorErrorTypes(models.TextChoices):
    model = "models", "Models"
    api = "api", "Api"
