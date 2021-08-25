from django.test import TestCase

from ..utils import create_base64_qrcode


class UtilsTests(TestCase):
    maxDiff = 1024

    def test_create_base64_qrcode(self):
        data = "44b322c32c5329b135e1"
        expected = (
            "iVBORw0KGgoAAAANSUhEUgAAAUoAAAFKAQAAAABTUiuoAAAB50lEQVR4n"
            "O2bzY3cMAxGHyMDe5Q72FLkDlJSkJLSgVXKdiAfA9j4cpA849nLziQYr4IlT/p5h"
            "w8gKNKibOJOy9/uJcFRRx111FFHn4laswGb2Mxs3AyWfXl6ugBHH0GTJKmAfo5Bm"
            "gmyiSBJ0i36HAGOPoIulxACSG9DHZjZcI4AR++w4d3cwFCeMLGcIcDRf0FTCbLpE"
            "wU4+jEaJc37ouao6jJJ6zkCHL3D2kmYDYBQZ5behhXY7PkCHH3YW4frp/y6QnVUv"
            "L2V+nStjlJr9CSJVAAIkkrYPRXbruZP1+po9Zakdc9RUYK4HtxYzb3VD7q8yKZlQ"
            "DObkQqYjUAeTxLg6D3WAodWCTYrQaQS2obHVifo5cBbOeSteU9etar3vNUJevQWc"
            "UUzYa834gpJq8dWN+ixgk+/BoDNyCMIthMEOPp3NeEhmOY6kuetvtB2ElZHlZvp1"
            "TxvdYJeYkuXXtaxtvC81SF67R1XS5JgGfx7q0v02jue44pNi1k7DhfvRvaD7hV8o"
            "ba26tpMON7oet7qFK1PMn7Uj+WwF4snCnD0ETSVzchmrbWVR2htyv60fjl0z0pRU"
            "B9ixHVQ/l4gv/6263uaDrQ62tBsZmYj2LS8vH+X0aa9aP3CqPlfC4466qijjv5H6"
            "B/hFU+U471mPQAAAABJRU5ErkJggg=="
        )

        result = create_base64_qrcode(data)

        self.assertEqual(result, expected)
