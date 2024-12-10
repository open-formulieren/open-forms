#!/usr/bin/env python
import sys
from pathlib import Path

import django

SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR.resolve()))


def check_for_null_submissions_in_temporary_uploads():
    from openforms.submissions.models import TemporaryFileUpload

    problematic_uploads = TemporaryFileUpload.objects.filter(submission__isnull=True)
    if problematic_uploads.exists():
        print("There are still legacy temporary uploads. You must clear those first.")
        return False

    return True


def main(skip_setup=False) -> bool:
    from openforms.setup import setup_env

    if not skip_setup:
        setup_env()
        django.setup()

    return check_for_null_submissions_in_temporary_uploads()


if __name__ == "__main__":
    main()
