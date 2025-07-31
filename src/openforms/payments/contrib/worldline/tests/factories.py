import factory
import factory.fuzzy

from ..constants import PaymentStatus
from ..models import WorldlineAccount, WorldlineMerchant


class WorldlineMerchantFactory(factory.django.DjangoModelFactory):
    label = "Merchant"
    pspid = "merchant"
    api_key = "key"
    api_secret = "sekrit"

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = WorldlineMerchant


class WorldlineAccountFactory(factory.django.DjangoModelFactory):
    webhook_key_id = factory.Faker("uuid4")
    webhook_key_secret = factory.Faker(
        "pystr", min_chars=40, max_chars=40
    )  # TODO: check if this is the correct amount? or use UUID here?

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = WorldlineAccount


class AmountOfMoneyFactory(factory.DictFactory):
    amount = factory.Faker("pyint")
    currency_code = factory.Faker("currency_code")


class ReferencesFactory(factory.DictFactory):
    merchant_reference = factory.Faker(
        "pystr_format", string_format="AcmeOrder####{{random_int}}"
    )
    payment_reference = factory.Faker("pystr_format", string_format="#{{random_int}}")


class CardFactory(factory.DictFactory):
    card_number = factory.Faker(
        "pystr_format", string_format="***********####{{random_int}}"
    )
    expiry_date = factory.Faker("pystr_format", string_format="####{{random_int}}")


class FraudResultsFactory(factory.DictFactory):
    avs_result = factory.Faker("pystr_format", string_format="#{{random_int}}")
    cvv_result = factory.Faker("pystr_format", string_format="#{{random_int}}")
    fraud_service_result = "no-advice"


class ThreeDSecureResultsFactory(factory.DictFactory):
    authentication_amount = factory.SubFactory(AmountOfMoneyFactory)


class CardPaymentMethodSpecificOutputFactory(factory.DictFactory):
    payment_product_id = factory.Faker("pyint")
    authorisation_code = factory.Faker("pyint")
    card = factory.SubFactory(CardFactory)
    fraud_results = factory.SubFactory(FraudResultsFactory)
    three_d_secure_results = factory.SubFactory(ThreeDSecureResultsFactory)


class PaymentOutputFactory(factory.DictFactory):
    amount_of_money = factory.SubFactory(AmountOfMoneyFactory)
    references = factory.SubFactory(ReferencesFactory)
    payment_method = "card"
    card_payment_method_specific_output = factory.SubFactory(
        CardPaymentMethodSpecificOutputFactory
    )


class StatusOutputFactory(factory.DictFactory):
    is_cancellable = True
    status_code = factory.Faker("pyint")
    status_code_change_date_time = factory.Faker(
        "pystr_format", string_format="##############{{random_int}}"
    )
    is_authorized = True


class PaymentRequestFactory(factory.DictFactory):
    id = factory.Faker(
        "pystr_format", string_format="##############################{{random_int}}"
    )

    payment_output = factory.SubFactory(PaymentOutputFactory)
    status = factory.fuzzy.FuzzyChoice(PaymentStatus.values)
    status_output = factory.SubFactory(StatusOutputFactory)


# see https://docs.connect.worldline-solutions.com/documentation/webhooks/event-structure/
class WebhookEventRequestFactory(factory.DictFactory):
    id = factory.Faker("uuid4")
    api_version = "v1"
    type = "payment.created"
    merchant_id = factory.Faker("pyint")
    payment = factory.SubFactory(PaymentRequestFactory)
