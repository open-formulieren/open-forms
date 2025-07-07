#!/usr/bin/env python
#
# Lint the dependencies for unexpected non-PyPI dependencies.
import sys
from pathlib import Path
from urllib.parse import urlparse

ALLOWLIST = []

ROOT_DIR = Path(__file__).parent.parent.resolve()


def main():
    input_file = ROOT_DIR / "requirements" / "base.in"
    allowed_paths = [f"/{repo}" for repo in ALLOWLIST]
    violations = []
    with open(input_file) as base_in:
        for line in base_in:
            line = line.strip()
            # ignore comments
            if line.startswith("#"):
                continue

            # regular dependency
            if not line.startswith("git+"):
                continue

            parsed = urlparse(line)
            # check for allowlist
            if any(parsed.path.startswith(path) for path in allowed_paths):
                continue

            violations.append(line)

    if violations:
        sys.stderr.write("The following dependencies were unexpected:\n")
        for violation in violations:
            sys.stderr.write(f"*  {violation}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
