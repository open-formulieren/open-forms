from datetime import date

from ..api_models import Price, PriceOption, ProductType


def create_price_option(uuid):
    return PriceOption(
        id=uuid,
        amount="10.00",
        description="description",
    )


def create_price(price_uuid, option_uuid):
    return Price(
        id=price_uuid,
        valid_from=date.today(),
        options=[
            create_price_option(option_uuid).__dict__
        ],  # __dict__ is needed for zgw_consumers.api_models.Model _type_cast
    )


def create_product_type(product_uuid, price_uuid, option_uuid):
    return ProductType(
        id=product_uuid,
        current_price=create_price(price_uuid, option_uuid),
        upl_uri="http://standaarden.overheid.nl/owms/terms/AangifteVertrekBuitenland",
        upl_name="aangifte vertrek buitenland",
        name="aangifte vertrek buitenland",
    )
