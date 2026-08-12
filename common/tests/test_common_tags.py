from decimal import Decimal

from django.template import Context, Template
from django.test import SimpleTestCase


class FormatCediFilterTests(SimpleTestCase):
    def test_formats_whole_cedi_amounts(self):
        rendered = Template("{% load common_tags %}{{ value|format_cedi:0 }}").render(
            Context({"value": Decimal("12500")})
        )
        self.assertEqual(rendered, "GH₵12,500")

    def test_formats_zero(self):
        rendered = Template("{% load common_tags %}{{ value|format_cedi:0 }}").render(Context({"value": 0}))
        self.assertEqual(rendered, "GH₵0")
