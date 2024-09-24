#!/usr/bin/env python
import sys
from pathlib import Path

import django

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def main() -> None:
    from openforms.setup import setup_env

    setup_env()
    django.setup()

    from openforms.config.constants import UploadFileType
    from openforms.config.models import GlobalConfiguration

    config = GlobalConfiguration.get_solo()
    if "application/zip" not in config.form_upload_default_file_types:
        return

    config.form_upload_default_file_types.remove("application/zip")
    config.form_upload_default_file_types.append(UploadFileType.zip)
    config.save(update_fields=("form_upload_default_file_types",))


if __name__ == "__main__":
    main()
