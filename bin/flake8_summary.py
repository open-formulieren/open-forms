#!/usr/bin/env python
import sys


def main(flake8_output: str):
    for line in flake8_output.splitlines():
        file, line, column, error = line.split(":", 3)
        print(f"| {file} | {line} | {column} | {error.strip()} |")


if __name__ == "__main__":
    main(sys.argv[1])
