from typing import Tuple

from django.apps import apps
from django.core.management import BaseCommand

DEPRECATED_TAGS = ("{% display_value",)


MODELS_AND_FIELDS = (
    (
        "config.GlobalConfiguration",
        (
            "submission_confirmation_template",
            "confirmation_email_subject",
            "confirmation_email_content",
        ),
    ),
    (
        "forms.Form",
        (
            "submission_confirmation_template",
            "explanation_template",
        ),
    ),
)


class Command(BaseCommand):
    help = "Detect deprecated template tag usage in user-templates"

    def handle(self, **options):
        for model, fields in MODELS_AND_FIELDS:
            self.check_model(model, fields)

        self.stdout.write("Done checking.")

    def check_model(self, model: str, fields: Tuple[str]):
        model_cls = apps.get_model(model)

        for tag in DEPRECATED_TAGS:
            filters = {f"{field}__contains": tag for field in fields}
            queryset = model_cls.objects.filter(**filters).values_list("id", flat=True)
            if not queryset:
                continue
            self.stdout.write(
                f"Model {model} instances containing deprecated tag '{tag}': {', '.join(queryset)}"
            )
