import os

from dotenv import load_dotenv
from onlinepayments.sdk.domain.create_hosted_checkout_request import (
    CreateHostedCheckoutRequest,
)
from onlinepayments.sdk.factory import Factory

load_dotenv()

api_key = os.environ["WORLDLINE_API_KEY"]
api_secret = os.environ["WORLDLINE_API_SECRET"]
merchant_id = os.environ["WORLDLINE_MERCHANT_ID"]

client = Factory.create_client_from_file("payments_sdk.prp", api_key, api_secret)
merchant_client = client.merchant(merchant_id)


order_dict = {"order": {"amountOfMoney": {"currencyCode": "EUR", "amount": 123}}}

hosted_checkout_client = client.merchant(merchant_id).hosted_checkout()
hosted_checkout_request = CreateHostedCheckoutRequest()
hosted_checkout_request.from_dictionary(order_dict)

hosted_checkout_response = hosted_checkout_client.create_hosted_checkout(
    hosted_checkout_request
)

breakpoint()
