.. _developers_tokens:

==================
Timestamped tokens
==================

Open Forms includes a base token generator implementation which generates timestamped
salted Hashed Message Authentication Code (S-HMAC) tokens. These tokens invalidate
after a configured number of days and/or when the hash input state has changed.

The tokens are especially well suited for one-time use and protect against replay
attacks, without having to store state in the database.

As a developer needing such tokens, you can use the base class for the bulk of the
work, which is inspired from Django's password reset token generator.

.. autoclass:: openforms.tokens.BaseTokenGenerator
   :members:
