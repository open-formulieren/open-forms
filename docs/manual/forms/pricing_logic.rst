.. _pricing_logic:

===============
Pricing Logic
===============

Open Forms supports three modes of determining the price for a product or service
associated with a form: (1) static, (2) dynamic, (3) from variable.

Static
======

The product price is fixed by the product configuration.

Dynamic
=======

*This mode will be deprecated in a future version. Determining the price via logic rules will be done via user-
defined variables. See below.*

The product price is determined dynamically on the basis of rules. For example, if the day the form is accessed
and completed on or before April 1st, the price for the product is 9.99; afterwards the price is raised to 15.99.

In order to recreate this example:

1. Create a new form
2. Navigate to **Product** and create a new product with name and price equal to 15.99
3. Navigate to **Change form > Product and payment** and under **Pricing logic** choose **Use pricing
   rules to determine the price**
4. Create two rules:
    If **today** > **is less than or equal to** > **the value** > **04/01/2023** > then the price is € > **9.99**

    If **today** > **is greater than** > **the value** > **04/01/2023** > then the price is € > **15.99**


From Variable
=============

The price is determined from a separate user-defined variable, the value of which is turn
determined by a combination of logic rules and the price fixed in the product configuration.

For example, the "unit price" for a certain service (``product``) provided by the municipality is
€ 99.99,-. The total price to be paid by the client (``order``) depends on whether they are
eligible for a discount, which is determined by their KvK or BSN authentication number. If that
number is in list 1, they receive a discount of 50%, if it is in list 2, they receive a discount
of 25%, otherwise they pay the full price.

In order to recreate the previous example:

1. Create a new form
2. Navigate to **Change form > Variables > User defined** and create a variable ``order`` with datatype ``float``
3. Navigate to **Product** and create a new product with name and price equal to 99.99
4. Navigate to **Change form > Logic** and create two logic rules:

    If **Authentication KVK (auth_kvk)** > **in** > **the list** > (*[1, 2, 3]*) > then **set the value of
    the variable** > **order** > to > **"0.5 x {{ product.price }}**"

    If **Authentication KVK (auth_kvk)** > **in** > **the list** > (*[4, 5, 6]*) > then **set the value of
    the variable** > **order** > to > **"0.75 x {{ product.price }}**"

5. Navigate to **Change form > Product and payment** and under **Pricing logic** choose **Use logic rules to
determine the value of user-defined variables based on product price**
6. From the dropdown menu select the variable ``order``
