# Source: https://github.com/vbabiy/djangorestframework-camel-case/blob/master/djangorestframework_camel_case/util.py

# Copyright (c) 2013, Vitaly Babiy
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of Django REST Framework JSON CamelCase nor the names of
#   its contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import re

from django.core.files import File
from django.http import QueryDict


def get_underscoreize_re(options):
    if options.get("no_underscore_before_number"):
        pattern = r"([a-z]|[0-9]+[a-z]?|[A-Z]?)([A-Z])"
    else:
        pattern = r"([a-z]|[0-9]+[a-z]?|[A-Z]?)([A-Z0-9])"
    return re.compile(pattern)


def camel_to_underscore(name, **options):
    underscoreize_re = get_underscoreize_re(options)
    return underscoreize_re.sub(r"\1_\2", name).lower()


def _get_iterable(data):
    if isinstance(data, QueryDict):
        return data.lists()
    else:
        return data.items()


def underscoreize(data, **options):
    if isinstance(data, dict):
        new_dict = {}
        for key, value in _get_iterable(data):
            if isinstance(key, str):
                new_key = camel_to_underscore(key, **options)
            else:
                new_key = key
            new_dict[new_key] = underscoreize(value, **options)

        if isinstance(data, QueryDict):
            new_query = QueryDict(mutable=True)
            for key, value in new_dict.items():
                new_query.setlist(key, value)
            return new_query
        return new_dict
    if is_iterable(data) and not isinstance(data, (str, File)):
        return [underscoreize(item, **options) for item in data]

    return data


def is_iterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return True
