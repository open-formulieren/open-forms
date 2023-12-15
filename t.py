from pathlib import Path
import libcst as cst
from libcst.codemod import CodemodContext
from django_autotyping.stubbing.codemod import TestVisitor

import sys
sys.path.append("src/")

import os
os.environ["DJANGO_SETTINGS_MODULE"] = "openforms.conf.dev"

from django.apps import apps
from django import setup
setup()



t = TestVisitor(CodemodContext(scratch={"django_models": apps.get_models()}))

result = t.transform_module(cst.parse_module(Path("typings/django-stubs/db/models/fields/related.pyi").read_text()))
with open("test.pyi", "w") as fp:
    fp.write(result.code)
# print(result.code)


# print(cst.parse_module("""
# def __init__(self: Class[A | int, B], to: str, *, null: Literal[True] = ...):
#     ...
# """))