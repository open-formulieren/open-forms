from django.db import models

from csp_post_processor.fields import CSPPostProcessedWYSIWYGField


class Model(models.Model):
    wysiwyg = CSPPostProcessedWYSIWYGField(
        models.TextField(
            "some verbose name",
            blank=True,
            null=False,
        )
    )
