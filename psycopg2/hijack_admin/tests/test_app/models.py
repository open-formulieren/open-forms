from django.conf import settings
from django.db import models


class BasicModel(models.Model):
    pass


class RelatedModel(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='related', on_delete=models.CASCADE)
