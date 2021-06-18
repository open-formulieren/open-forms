import os.path
import sys
from dataclasses import dataclass
from typing import Tuple

from django.core.management import BaseCommand

import black
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
    name: str
    path: str
    labels: Tuple[str] = None


simple_types = (
    "string",
    "integer",
    "number",
    "boolean",
)

preferred_content_types = [
    "application/hal+json",
    "application/json",
    "text/json",
]


def select_call(root_schema, api_path):
    try:
        content_types = glom(
            root_schema, Path("paths", api_path, "get", "responses", "200", "content")
        )
    except GlomError as e:
        print(e)
        return None

    for t in preferred_content_types:
        try:
            return content_types[t]
        except KeyError:
            pass
    return None


def select_schema(root_schema, api_schema):
    try:
        return glom(root_schema, Path("components", "schemas", api_schema))
    except GlomError as e:
        print(e)
        return None


def generate_prefill_from_spec_url(
    url, api_path="", api_schema="", use_embeds=False, command=""
):
    schema_fetcher = SchemaFetcher()
    root_schema = schema_fetcher.fetch(url)

    # find the call with the http parameters we're interested in
    if not api_path and not api_schema:
        raise Exception("pass either api_path or api_schema")

    elif api_path:
        content_type = select_call(root_schema, api_path)
        if not content_type:
            raise NotImplementedError(
                f"cannot find suitable content-type: {preferred_content_types}"
            )

        if "$ref" in content_type["schema"]:
            schema = json_path(root_schema, content_type["schema"]["$ref"])
        else:
            schema = content_type["schema"]
        if not schema:
            raise NotImplementedError(f"cannot find suitable schema")

    elif api_schema:
        schema = select_schema(root_schema, api_schema)
        if "$ref" in schema:
            schema = json_path(root_schema, schema["$ref"])
        if not schema:
            raise NotImplementedError(f"cannot find suitable schema")

    else:
        raise Exception("cannot pass both api_path and api_schema")

    # run the actual thing
    raw_props = list(
        generate_prefill_from_schema(root_schema, schema, use_embeds=use_embeds)
    )

    names = [p.name for p in raw_props]
    if list(sorted(names)) != list(sorted(set(names))):
        for n in set(names):
            names.remove(n)
        raise Exception(f"generated names not unique, duplicates: {names}")

    yield "from django.utils.translation import gettext_lazy as _"
    yield "from djchoices import ChoiceItem, DjangoChoices"
    yield "class Attributes(DjangoChoices):"
    yield '    """'
    yield "    this code was (at some point) generated from an API-spec, so names and labels are in Dutch if the spec was Dutch"
    yield ""
    yield f"    spec:    {url}"
    if api_path:
        yield f"    path:    {api_path}"
    if api_schema:
        yield f"    schema:  {api_schema}"
    if command:
        yield f"    command: {command}"
    yield '    """'

    for c in sorted(raw_props, key=lambda o: o.name):
        label = " > ".join(c.labels)  # .replace(" > []", "[]")
        label = f'_("{label}")'
        yield f'    {c.name} = ChoiceItem("{c.path}", {label})'

    yield ""


def generate_prefill_from_schema(
    root_schema: dict,
    schema: dict,
    use_embeds: bool = False,
):
    if schema["type"] == "object":
        for prop, sub_schema in schema["properties"].items():
            yield from generate_prop(
                root_schema, sub_schema, prop, use_embeds=use_embeds
            )
    elif schema["type"] == "array":
        # untested code... good luck
        yield from generate_prop(
            root_schema, schema["items"], "[]", use_embeds=use_embeds
        )
    else:
        raise NotImplementedError(f"not object type: {schema['type']}")


def generate_prop(
    root_schema, schema, prop, parent_path="", parent_labels=None, use_embeds=False
):
    if "." in prop:
        # supporting this was out of scope at the time
        # see note with possible solution: https://github.com/open-formulieren/open-forms/pull/384/files#r644045666
        raise NotImplementedError(
            "properties cannot contain '.' without modifications to the code"
        )

    if "$ref" in schema:
        schema = json_path(root_schema, schema["$ref"])
        if use_embeds:
            path = (
                f"{parent_path}._embedded.{prop}"
                if parent_path
                else f"_embedded.{prop}"
            )
        else:
            path = f"{parent_path}.{prop}" if parent_path else prop
    else:
        path = f"{parent_path}.{prop}" if parent_path else prop

    label = schema.get("title", prop)
    if label:
        label = (label,)
        if parent_labels:
            label = parent_labels + label
    else:
        label = parent_labels or tuple()

    if schema["type"] == "object":
        if "properties" in schema:
            for prop, sub_schema in schema["properties"].items():
                # if "$ref" in sub_schema:
                #     sub_schema = json_path(root_schema, sub_schema["$ref"])
                yield from generate_prop(
                    root_schema, sub_schema, prop, path, label, use_embeds=use_embeds
                )
    elif schema["type"] == "array":
        if "items" in schema:
            sub_schema = schema["items"]
            # if "$ref" in sub_schema:
            #     sub_schema = json_path(root_schema, sub_schema["$ref"])
            # path = f"{path}[]"
            # label = label + ("[]",)
            yield from generate_prop(
                root_schema, sub_schema, "[]", path, label, use_embeds=use_embeds
            )
    elif schema["type"] in simple_types:
        choice = Choice(
            path.replace("_embedded.", "").replace("[]", "i").replace(".", "_"),
            path.replace(".[]", "[]"),
            label,
        )
        yield choice
    else:
        raise NotImplementedError(f"not known type: {schema['type']}")


def format_command(options, prefs):
    command = os.path.splitext(os.path.basename(__file__))[0]
    args = list()
    for p in prefs:
        if isinstance(p, tuple):
            for pp in p:
                if options.get(pp) is not None:
                    args.append((pp, options[pp]))
                    break
        else:
            if options.get(p) is not None:
                args.append((p, options[p]))

    parts = list()
    for a, v in args:
        if isinstance(v, bool):
            if v:
                parts.append(f"--{a}")
        else:
            parts.append(f"--{a} {v}")
    # args = " ".join(list(sys.argv)[1:])
    arguments = " ".join(parts)
    return f"manage.py {command} {arguments}"


class Command(BaseCommand):
    help = "Generate prefill attributes from API spec"

    def add_arguments(self, parser):
        parser.add_argument(
            "--schema",
            action="store",
            type=str,
            help="API schema",
            default=None,
        )
        parser.add_argument(
            "--path",
            action="store",
            type=str,
            help="API resource",
            default=None,
        )

        parser.add_argument(
            "--service",
            action="store",
            type=int,
            help="ID of a ZGWConsumers Service",
            default=None,
        )
        parser.add_argument(
            "--url",
            action="store",
            type=str,
            help="URL to schema",
            default=None,
        )

        parser.add_argument(
            "--embedded",
            action="store_true",
            help="Add '_embedded.' in paths for $refs",
            default=False,
        )

    def handle(self, **options):
        if options["service"] and options["url"]:
            self.stderr.write(f"use either --service or --url (not both)")
            return

        if options["path"] and options["schema"]:
            self.stderr.write(f"use either --path or --schema (not both)")
            return

        if options["service"]:
            service = Service.objects.filter(id=options["service"]).first()
            if not service:
                self.stderr.write(f"cannot find service with ID {options['service']}")
                return
            if not service.oas:
                self.stderr.write(f"cannot find service ID {options['service']}")
                return
            # write-back for better generated command comment
            options["url"] = service.oas

        # proceed
        url = options["url"]
        if not url:
            # be helpful and suggest services
            self.stdout.write("service:")
            for service in Service.objects.order_by("id"):
                self.stdout.write(f"{service.id} {service}")
            return

        if url and not options["path"] and not options["schema"]:
            # be helpful and suggest paths and schemas
            schema = SchemaFetcher().fetch(url)

            if schema["paths"]:
                self.stdout.write("path:")
                for path, attrs in schema["paths"].items():
                    self.stdout.write(f"  {path}")

            if schema["components"]["schemas"]:
                self.stdout.write("schema:")
                for name in schema["components"]["schemas"].keys():
                    self.stdout.write(f"  {name}")

            return

        # run generations
        command = format_command(
            options, [("path", "schema"), ("url", "service"), "embedded"]
        )
        output = list(
            generate_prefill_from_spec_url(
                url,
                options["path"],
                options["schema"],
                options["embedded"],
                command=command,
            )
        )

        # paint it black
        try:
            mode = black.FileMode()
            out = black.format_str("\n".join(output), mode=mode)
            self.stdout.write(out)
        except black.InvalidInput as e:
            self.stdout.write("\n".join(output))
            self.stdout.write("\n")
            raise e
