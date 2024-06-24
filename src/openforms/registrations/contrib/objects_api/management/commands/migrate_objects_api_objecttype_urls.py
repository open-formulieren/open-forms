from django.core.management import BaseCommand

from openforms.forms.models import FormRegistrationBackend

from ...client import get_objecttypes_client
from ...models import ObjectsAPIGroupConfig


class Command(BaseCommand):
    help = (
        "Migrate existing Objects API form registration backends "
        "to switch from an objecttype URL to a name"
    )

    def handle(self, **options):
        for registration_backend in FormRegistrationBackend.objects.filter(backend="objects_api"):
            backend_name = registration_backend.name

            if objecttype_url := registration_backend.options.get("objecttype_url"):
                group = ObjectsAPIGroupConfig.objects.get(pk=registration_backend.options["objects_api_group"])

                with get_objecttypes_client(group) as objecttypes_client:
                    objecttypes = objecttypes_client.list_objecttypes()

                objecttype_name: str | None = next(
                    (
                        objecttype["name"]
                        for objecttype in objecttypes
                        if objecttype["url"] == objecttype_url
                    ),
                    None,
                )

                if objecttype_name is None:
                    self.stdout.write(f"Unable to find the objecttype {objecttype_url} for form backend {backend_name!r}")
                else:
                    self.stdout.write(f"Switching from URL {objecttype_url} to name {objecttype_name} for form backend {backend_name!r}")
                    del registration_backend.options["objecttype_url"]
                    registration_backend.options["objecttype_name"] = objecttype_name

                registration_backend.save()
