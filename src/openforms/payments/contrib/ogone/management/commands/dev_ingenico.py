from pprint import pprint

from django.core.management.base import BaseCommand

import requests

from openforms.payments.contrib.ogone.data import OgoneRequestParams
from openforms.payments.contrib.ogone.signing import calculate_shasign


class Command(BaseCommand):
    """
    temporary command for dev
    TODO remove before merge
    """

    help = "Creates an initial superuser account and mails the credentials to the specified email"

    def add_arguments(self, parser):
        parser.add_argument(
            "--merchant_id",
            help="Specifies the username for the superuser.",
            type=int,
            default=1,
        )

    def handle(self, *args, **options):
        # example from the docs
        url = "https://ogone.test.v-psp.com/ncol/test/orderstandard_utf8.asp"

        params = OgoneRequestParams(
            AMOUNT=1500,
            CURRENCY="EUR",
            LANGUAGE="en_US",
            ORDERID=1234,
            PSPID="MyPSPID",
        )
        passphrase = "Mysecretsig1875!?"
        data = params.get_dict()
        data["SHASIGN"] = calculate_shasign(data, passphrase, "sha1")

        res = requests.post(url, data=data)
        res.raise_for_status()
        print(res.text)
        pprint(res)
