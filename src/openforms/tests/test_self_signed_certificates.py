# SPDX-License-Identifier: EUPL-1.2
# Copyright (C) 2021 Dimpact
# Taken from Open Zaak
"""
Test support for self-signed certificates.

This works by manipulating :module:`requests` CA_BUNDLE parameters, appending any
specified (root) certificates to the existing requests bundle. None of this is
Django specific.

Note that you should have the CI docker-compose running with the mock endpoints, which
uses the self-signed certificates.
"""
import os
from unittest import TestCase, skipIf

from django.conf import settings

import requests

from openforms.setup import load_self_signed_certs

from .utils import can_connect

CERTS_DIR = os.path.join(settings.BASE_DIR, "docker", "certs")

EXTRA_CERTS_ENVVAR = "EXTRA_VERIFY_CERTS"

HOST = "localhost:9001"
PUBLIC_INTERNET_HOST = "github.com:443"


class SelfSignedCertificateTests(TestCase):

    root_cert = os.path.join(CERTS_DIR, "openforms.crt")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._original_requests_ca = os.environ.get("REQUESTS_CA_BUNDLE")
        if "REQUESTS_CA_BUNDLE" in os.environ:
            del os.environ["REQUESTS_CA_BUNDLE"]
        cls._original_certs = os.environ.get(EXTRA_CERTS_ENVVAR)
        os.environ[EXTRA_CERTS_ENVVAR] = cls.root_cert
        load_self_signed_certs()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        if cls._original_certs is None:
            del os.environ[EXTRA_CERTS_ENVVAR]
        else:
            os.environ[EXTRA_CERTS_ENVVAR] = cls._original_certs

        if cls._original_requests_ca is not None:
            os.environ["REQUESTS_CA_BUNDLE"] = cls._original_requests_ca

    @skipIf(not can_connect(HOST), "Can't connect to host")
    def test_self_signed_ok(self):
        """
        Assert that self-signed certificates can be used.
        """
        response = requests.get(f"https://{HOST}")

        self.assertEqual(response.status_code, 200)

    @skipIf(not can_connect(PUBLIC_INTERNET_HOST), "Can't connect to host")
    def test_public_ca_ok(self):
        """
        Assert that the existing certifi bundle is not completely replaced.
        """
        response = requests.get(f"https://{PUBLIC_INTERNET_HOST}")

        self.assertEqual(response.status_code, 200)
