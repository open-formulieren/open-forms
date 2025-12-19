from collections.abc import Mapping
from typing import Literal

from django.core.management import BaseCommand

from ...models import Form

type NewRendererState = Literal["enabled", "disabled"]


class Command(BaseCommand):
    help = "Enable/disable the new renderer for all forms."

    def add_arguments(self, parser):
        parser.add_argument(
            "--state",
            choices=["enabled", "disabled"],
            required=True,
            help="Desired state of the new renderer",
        )

    def handle(self, **options):
        state: NewRendererState = options["state"]

        state_enable_flag_mapping: Mapping[NewRendererState, bool] = {
            "enabled": True,
            "disabled": False,
        }
        use_new_renderer: bool = state_enable_flag_mapping[state]

        updated_count = Form.objects.exclude(
            new_renderer_enabled=use_new_renderer
        ).update(new_renderer_enabled=use_new_renderer)

        self.stdout.write(f"New renderer has been {state} for {updated_count} form(s).")
