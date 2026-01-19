import structlog

from ..celery import app
from .models import Product

logger = structlog.stdlib.get_logger(__name__)


# @TODO remove function, and use actual `get products client` func
def get_client():
    return None


# @TODO change type, perhaps update logic
def get_product_price(product_type: dict[str, str | list[str] | list[list[str]]]):
    product_price = 0.0

    if (
        (prices := product_type.prijzen)
        and len(prices) > 0
        and len(prices[0].prijsopties) > 0
    ):
        product_price = prices[0].prijsopties[0].bedrag

    return product_price


@app.task(ignore_result=True)
def update_products():
    """Activate all the forms that should be activated by the specific date and time."""

    products = Product.objects.all()

    with get_client() as client:
        client_product_types = client.fetch_product_types()
        for product_type in client_product_types:
            product = products.filter(product_type_uuid=product_type.uuid).first()
            if product:
                logger.info("update_product_type", product_type_uuid=product_type.uuid)
                product.name = product_type.naam
                product.price = get_product_price(product_type)
                product.information = product_type.samenvatting
            else:
                logger.info("create_product_type", product_type_uuid=product_type.uuid)
                Product.objects.create(
                    product_type_uuid=product_type.uuid,
                    name=product_type.naam,
                    price=get_product_price(product_type),
                    information=product_type.samenvatting,
                )
