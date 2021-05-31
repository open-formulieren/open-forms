import json
import os.path
from collections import OrderedDict
from dataclasses import dataclass
from json import JSONDecodeError
from typing import List, Tuple

import black
from django.core.management import BaseCommand
from glom import GlomError, Path, glom
from zds_client.oas import SchemaFetcher
from zgw_consumers.models import Service


def json_path(obj, reference):
    # simplistic json-path
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
    "integer",
    "number",
    "boolean",
)
preferred_content_types = [
    "application/hal+json",
    "application/json",
]


def select_call(root_schema, api_path):
    try:
        content_types = glom(
            root_schema, Path("paths", api_path, "get", "responses", "200", "content")
        )
    except GlomError as e:
        print(e)
        return

    for t in preferred_content_types:
        try:
            return content_types[t]
        except KeyError:
            pass
    return None


def generate_prefill_from_spec_url(url, api_path, word_map, output):
    schema_fetcher = SchemaFetcher()
    root_schema = schema_fetcher.fetch(url)

    # find the call with the http parameters we're interested in
    content_type = select_call(root_schema, api_path)

    if not content_type:
        raise NotImplementedError(
            f"cannot find suitable content-type: {preferred_content_types}"
        )

    if "$ref" in content_type["schema"]:
        ref = content_type["schema"]["$ref"]
        schema = json_path(root_schema, ref)
    else:
        schema = content_type["schema"]
        raise NotImplementedError(f"cannot handle embedded schema here")

    props = list()

    generate_prefill_from_schema(root_schema, props, word_map, schema)

    output.append("from django.utils.text import format_lazy")
    output.append("from django.utils.translation import gettext_lazy as _")
    output.append("from django.utils.translation import pgettext_lazy as pg")
    output.append("from djchoices import ChoiceItem, DjangoChoices")
    output.append("")
    output.append("class Attributes(DjangoChoices):")
    output.append(f"    # schema: {url}")
    output.append(f"    # path:   {api_path}")
    output.append("")

    for c in sorted(props, key=lambda o: o.name):
        # label = " > ".join(word_map[label] for label in c.label)
        # label = f'_("{label}")'

        if len(c.label) == 1:
            # label = f'_("{c.label[0]}")'
            label = f'pg("{c.label[0]}", "{word_map[c.label[0]]}")'
        else:
            fmt = " > ".join("{}" for i in range(len(c.label)))
            # parts = ", ".join(f'_("{word_map[label]}")' for label in c.label)
            parts = ", ".join(
                f'pg("{label}", "{word_map[label]}")' for label in c.label
            )
            label = f"format_lazy('{fmt}', {parts})"
        output.append(f'    {c.name} = ChoiceItem("{c.path}", {label})')


def generate_prefill_from_schema(
    root_schema: dict,
    props: List,
    words: dict,
    schema: dict,
    parent: str = "",
    labels: Tuple[str] = None,
):
    if schema["type"] == "object":
        for prop, sub_schema in schema["properties"].items():
            if "$ref" in sub_schema:
                sub_schema = json_path(root_schema, sub_schema["$ref"])
                if parent:
                    key = f"{parent}._embedded.{prop}"
                else:
                    key = f"_embedded.{prop}"
            else:
                if parent:
                    key = f"{parent}.{prop}"
                else:
                    key = prop

            label = sub_schema.get("title")
            if label:
                if label in words:
                    # label = words[label]
                    pass
                else:
                    words[label] = f"__{label}__"

                label = (label,)
                if labels:
                    # title = f"{titles} > {title}"
                    label = labels + label
            else:
                label = labels

            if sub_schema["type"] == "object":
                generate_prefill_from_schema(
                    root_schema, props, words, sub_schema, key, label
                )

            elif sub_schema["type"] == "array":
                # TODO array? nope
                pass

            elif sub_schema["type"] in simple_types:
                choice = Choice(
                    key.replace("_embedded.", "").replace(".", "_"),
                    key,
                    label,
                )
                props.append(choice)
            else:
                raise NotImplementedError(f"not known type: {schema['type']}")

    else:
        raise NotImplementedError(f"not object type: {schema['type']}")


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
            # be helpful and suggest services
            for service in Service.objects.order_by("id"):
                self.stdout.write(f"{service.id} {service}")
            return

        if url and not options["path"]:
            # be helpful and suggest paths
            schema = SchemaFetcher().fetch(url)
            for path, attrs in schema["paths"].items():
                self.stdout.write(path)
            return

        # read old words
        words_path = os.path.join(os.path.dirname(__file__), "translate-prefill.json")
        try:
            with open(words_path, "r") as f:
                word_map = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            word_map = dict()

        # run generations
        output = list()
        generate_prefill_from_spec_url(url, options["path"], word_map, output)

        mode = black.FileMode()
        out = black.format_str("\n".join(output), mode=mode)
        self.stdout.write(out)

        # save new words
        with open(words_path, "w") as f:
            s = OrderedDict()
            for k in sorted(word_map.keys()):
                s[k] = word_map[k]
            json.dump(s, f, indent=4)
