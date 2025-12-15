#!/usr/bin/env python
#
# The configuration for the README generation lives in ./config.json
#
# /// script
# dependencies = [
#   "jinja2~=3.1.6",
#   "requests~=2.32.4",
# ]
# ///
#
# Usage from the root of the repository:
#
# .. code-block:: bash
#
#     uv run ./docker/ci/generate_dockerhub_description.py
#
import json
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent.resolve()

GITHUB_ORG = "https://github.com/open-formulieren"
CONFIG_FILE_MASTER = (
    "https://raw.githubusercontent.com/open-formulieren/open-forms/master/"
    "docker/ci/config.json"
)
STABLE_PREFIX = "stable/"
EXTENSIONS_PREFIX = "all-extensions"
DOCKER_HUB_BASE = "https://hub.docker.com/v2/"
RE_SEMVER_TAG = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class TagConfiguration(TypedDict):
    gitRef: str
    tag: str | None
    hasExtensionsVariant: bool


class ExtensionConfiguration(TypedDict):
    name: str
    repo: str


def get_tag_names_on_dockerhub() -> list[str]:
    tag_names = []

    def _handle_response(response) -> dict:
        response.raise_for_status()
        response_data = response.json()
        nonlocal tag_names
        tag_names += [tag["name"] for tag in response_data["results"]]
        return response_data

    with requests.Session() as session:
        response = session.get(
            f"{DOCKER_HUB_BASE}/namespaces/openformulieren/repositories/open-forms/tags",
            params={"page_size": 10},
        )
        response_data = _handle_response(response)
        while next_page := response_data["next"]:
            response = session.get(next_page)
            response_data = _handle_response(response)

    # filter down to semver tags
    tag_names = [name for name in tag_names if RE_SEMVER_TAG.match(name)]
    return tag_names


def get_supported_tags(
    tag_configurations: list[TagConfiguration],
) -> Iterator["SupportedTag"]:
    existing_tags = get_tag_names_on_dockerhub()
    for config in tag_configurations:
        has_extensions = config["hasExtensionsVariant"]
        git_ref = config["gitRef"]
        is_stable = git_ref.startswith(STABLE_PREFIX)
        inferred_tag = git_ref.replace(STABLE_PREFIX, "", 1) if is_stable else git_ref
        tag = config["tag"] or inferred_tag
        explicit_supported_tag = SupportedTag(
            tag=tag, git_ref=git_ref, has_extensions=False
        )

        if not is_stable:
            yield explicit_supported_tag
            if has_extensions:
                yield SupportedTag(
                    tag=f"{EXTENSIONS_PREFIX}-{tag}",
                    git_ref=git_ref,
                    has_extensions=True,
                )
            continue

        # find the most recent concrete tag for the stable version
        major, minor, _ = inferred_tag.split(".")
        matching_tags = [
            tag for tag in existing_tags if tag.startswith(f"{major}.{minor}.")
        ]
        if not matching_tags:
            continue

        most_recent = sorted(
            matching_tags, key=lambda tag: int(tag.split(".")[-1]), reverse=True
        )[0]
        yield SupportedTag(tag=most_recent, git_ref=most_recent, has_extensions=False)
        yield explicit_supported_tag

        if has_extensions:
            yield SupportedTag(
                tag=f"{EXTENSIONS_PREFIX}-{most_recent}",
                git_ref=most_recent,
                has_extensions=True,
            )


def get_available_extensions(
    extension_configurations: list[ExtensionConfiguration],
) -> list["Extension"]:
    extensions = []
    for config in extension_configurations:
        extensions.append(
            Extension(name=config["name"], repository=f"{GITHUB_ORG}/{config['repo']}")
        )
    return extensions


def _get_config(current_branch: str | None):
    # no branch specified -> not on CI -> grab local config
    if current_branch is None or current_branch == "master":
        with (ROOT / "config.json").open("r") as config_file:
            return json.load(config_file)

    response = requests.get(CONFIG_FILE_MASTER)
    response.raise_for_status()
    return response.json()


def main(current_branch: str | None):
    config = _get_config(current_branch)
    supported_tags = list(get_supported_tags(config["supportedTags"]))
    extensions = get_available_extensions(config["availableExtensions"])
    context = {
        "github_org": GITHUB_ORG,
        "supported_tags": supported_tags,
        "extensions": extensions,
    }
    content = render_readme(context)
    readme_path = ROOT / "README.md"
    with readme_path.open("w") as outfile:
        outfile.write(content)
    print(f"README file written to {readme_path}")
    return


def render_readme(context: dict) -> str:
    env = Environment(loader=FileSystemLoader(ROOT), autoescape=select_autoescape())
    template = env.get_template("dockerhub_readme.md.j2")
    return template.render(context)


@dataclass
class SupportedTag:
    tag: str
    git_ref: str
    has_extensions: bool = False

    @property
    def dockerfile_url(self) -> str:
        return f"https://github.com/open-formulieren/open-forms/blob/{self.git_ref}/Dockerfile"


@dataclass
class Extension:
    name: str
    repository: str


if __name__ == "__main__":
    branch_name = sys.argv[1] if len(sys.argv) > 1 else None
    main(branch_name)
