from decimal import Decimal
from unittest import TestCase

from common.money import MONEY_QUANT, ZERO, quantize_money, to_api_amount, to_minor_units


class MoneyUtilsTests(TestCase):
    def test_quantize_money_rounds_half_up(self):
        self.assertEqual(quantize_money("10.005"), Decimal("10.01"))
        self.assertEqual(quantize_money(Decimal("99.994")), Decimal("99.99"))

    def test_to_minor_units_avoids_float_drift(self):
        self.assertEqual(to_minor_units(Decimal("19.99")), 1999)
        self.assertEqual(to_minor_units("0.01"), 1)

    def test_to_api_amount_preserves_two_decimals(self):
        self.assertEqual(to_api_amount(Decimal("49.50")), 49.50)

    def test_constants(self):
        self.assertEqual(MONEY_QUANT, Decimal("0.01"))
        self.assertEqual(ZERO, Decimal("0"))
