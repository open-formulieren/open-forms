#!/usr/bin/env python
import json
from pathlib import Path

INFILE = Path(".") / "src" / "openforms" / "js" / "lang" / "nl.json"


def main():
    with open(INFILE) as nl_translations:
        translations = json.load(nl_translations)

    for unique_id, trans_object in translations.items():
        # skip translated messages
        if trans_object["defaultMessage"] != trans_object["originalDefault"]:
            continue

        print(
            f"ID '{unique_id}' appears untranslated, defaultMessage: {trans_object['originalDefault']}"
        )


if __name__ == "__main__":
    main()
