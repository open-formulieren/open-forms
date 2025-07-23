import os

from dotenv import load_dotenv
from onlinepayments.sdk.domain.create_hosted_checkout_request import (
    CreateHostedCheckoutRequest,
)
from onlinepayments.sdk.factory import CommunicatorConfiguration, Factory

load_dotenv()

api_key = os.environ["WORLDLINE_API_KEY"]
api_secret = os.environ["WORLDLINE_API_SECRET"]
merchant_id = os.environ["WORLDLINE_MERCHANT_ID"]

base_api_url = "https://payment.preprod.direct.worldline-solutions.com"

communicator_configuration = CommunicatorConfiguration(
    api_endpoint=base_api_url,
    api_key_id=api_key,
    secret_api_key=api_secret,
    authorization_type="v1HMAC",
    integrator="openforms-test-sonny",
    connect_timeout=5000,
    socket_timeout=10000,
    max_connections=10,
)

communicator = Factory.create_communicator_from_configuration(
    communicator_configuration
)
client = Factory.create_client_from_communicator(communicator)
merchant_client = client.merchant(merchant_id)


order_dict = {"order": {"amountOfMoney": {"currencyCode": "EUR", "amount": 123}}}

hosted_checkout_client = merchant_client.hosted_checkout()
hosted_checkout_request = CreateHostedCheckoutRequest()
hosted_checkout_request.from_dictionary(order_dict)

hosted_checkout_response = hosted_checkout_client.create_hosted_checkout(
    hosted_checkout_request
)

breakpoint()
