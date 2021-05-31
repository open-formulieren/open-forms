import json
from dataclasses import dataclass

from django.core.management import BaseCommand

from glom import GlomError, Path, glom
from zds_client.oas import SchemaFetcher
from zgw_consumers.models import Service


def json_path(obj, reference):
    if reference[:2] == "#/":
        split_path = reference[2:].split("/")
        tmp = obj
        for parent in split_path:
            tmp = tmp.get(parent)

        return tmp

    raise NotImplementedError()


@dataclass()
class Choice:
    name: str = ""
    path: str = ""
    label: str = ""


simple_types = (
    "string",
    "number",
)


def generate_prefill_from_spec_url(url, api_path, file):
    schema_fetcher = SchemaFetcher()
    root_schema = schema_fetcher.fetch(url)

    # with open('schema.json', "w") as f:
    #     json.dump(root_schema, f)

    try:
        content_types = glom(
            root_schema, Path("paths", api_path, "get", "responses", "200", "content")
        )
    except GlomError as e:
        print(e)
        return

    preferred_types = [
        "application/hal+json",
        "application/json",
    ]
    content_type = None
    for t in preferred_types:
        try:
            content_type = content_types[t]
        except KeyError:
            pass
        else:
            break

    if not content_type:
        print(f"cannot find suitable content-type: {preferred_types}")
        return

    if "$ref" in content_type["schema"]:
        ref = content_type["schema"]["$ref"]
        schema = json_path(root_schema, ref)
    else:
        print(f"cannot handle embedded schema here")
        return

    props = list()

    generate_prefill_from_schema(root_schema, props, schema)

    file.write("class Attributes(DjangoChoices):")

    for c in sorted(props, key=lambda o: o.name):
        file.write(f'    {c.name} = ChoiceItem("{c.path}", _("{c.label}"))')


def generate_prefill_from_schema(root_schema, props, schema, parent=""):
    if schema["type"] == "object":
        for property, sub_schema in schema["properties"].items():
            if "$ref" in sub_schema:
                sub_schema = json_path(root_schema, sub_schema["$ref"])
                if parent == "":
                    p = f"_embedded.{property}"
                else:
                    p = f"{parent}._embedded.{property}" if parent else property
            else:
                p = f"{parent}.{property}" if parent else property

            if sub_schema["type"] in simple_types:
                choice = Choice(
                    p.replace("_embedded.", "").replace(".", "_"),
                    p,
                    sub_schema["title"],
                )
                props.append(choice)
            else:
                generate_prefill_from_schema(root_schema, props, sub_schema, p)


class Command(BaseCommand):
    help = "Generate prefill attributes from API spec"

    def add_arguments(self, parser):
        parser.add_argument(
            "service_id",
            action="store",
            type=int,
            help="ID of a ZGWConsumers Service",
            nargs="?",
            default=None,
        )
        parser.add_argument(
            "path",
            action="store",
            type=str,
            help="API resource",
            nargs="?",
            default=None,
        )
        parser.add_argument(
            "--url",
            action="store",
            type=str,
            help="STP test URL",
            nargs="?",
            default=None,
        )

    def handle(self, **options):
        url = None
        if options["service_id"]:
            service = Service.objects.filter(id=options["service_id"]).first()
            if not service:
                self.stderr.write(
                    f"cannot find service with ID {options['service_id']}"
                )
                return
            if not service.oas:
                self.stderr.write(f"cannot find service ID {options['service_id']}")
                return
            url = service.oas
        elif options["url"]:
            url = options["url"]

        if not url:
            for service in Service.objects.order_by("id"):
                self.stdout.write(f"{service.id} {service}")
            return

        if url and not options["path"]:
            schema = SchemaFetcher().fetch(url)
            for path, attrs in schema["paths"].items():
                self.stdout.write(path)
            return

        generate_prefill_from_spec_url(url, options["path"], self.stdout)
