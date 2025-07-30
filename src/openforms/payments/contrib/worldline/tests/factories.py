import factory
import factory.fuzzy

from ..constants import PaymentStatus
from ..models import WorldlineMerchant


class WorldlineMerchantFactory(factory.django.DjangoModelFactory):
    label = "Merchant"
    pspid = "merchant"
    api_key = "key"
    api_secret = "sekrit"

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = WorldlineMerchant


class AmountOfMoneyFactory(factory.DictFactory):
    amount = factory.Faker("pyint")
    currencyCode = factory.Faker("currency_code")


class ReferencesFactory(factory.DictFactory):
    merchantReference = factory.Faker(
        "pystr_format", string_format="AcmeOrder####{{random_int}}"
    )
    paymentReference = factory.Faker("pystr_format", string_format="#{{random_int}}")


class CardFactory(factory.DictFactory):
    cardNumber = factory.Faker(
        "pystr_format", string_format="***********####{{random_int}}"
    )
    expiryDate = factory.Faker("pystr_format", string_format="####{{random_int}}")


class FraudResultsFactory(factory.DictFactory):
    avsResult = factory.Faker("pystr_format", string_format="#{{random_int}}")
    cvvResult = factory.Faker("pystr_format", string_format="#{{random_int}}")
    fraudServiceResult = "no-advice"


class ThreeDSecureResultsFactory(factory.DictFactory):
    authenticationAmount = factory.SubFactory(AmountOfMoneyFactory)


class CardPaymentMethodSpecificOutputFactory(factory.DictFactory):
    paymentProductId = factory.Faker("pyint")
    authorisationCode = factory.Faker("pyint")
    card = factory.SubFactory(CardFactory)
    fraudResults = factory.SubFactory(FraudResultsFactory)
    threeDSecureResults = factory.SubFactory(ThreeDSecureResultsFactory)


class PaymentOutputFactory(factory.DictFactory):
    amountOfMoney = factory.SubFactory(AmountOfMoneyFactory)
    references = factory.SubFactory(ReferencesFactory)
    paymentMethod = "card"
    cardPaymentMethodSpecificOutput = factory.SubFactory(
        CardPaymentMethodSpecificOutputFactory
    )


class StatusOutputFactory(factory.DictFactory):
    isCancellable = True
    statusCode = factory.Faker("pyint")
    statusCodeChangeDateTime = factory.Faker(
        "pystr_format", string_format="##############{{random_int}}"
    )
    isAuthorized = True


class PaymentResponseFactory(factory.DictFactory):
    id = factory.Faker(
        "pystr_format", string_format="##############################{{random_int}}"
    )
    paymentOutput = factory.SubFactory(PaymentOutputFactory)
    status = factory.fuzzy.FuzzyChoice(PaymentStatus.values)
    statusOutput = factory.SubFactory(StatusOutputFactory)
