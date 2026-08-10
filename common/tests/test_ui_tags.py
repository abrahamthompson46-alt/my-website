"""Tests for shared UI template tags."""

from django.template import Context, Template
from django.test import SimpleTestCase


class UiButtonTagTests(SimpleTestCase):
    def test_url_name_renders_as_link(self):
        template = Template(
            "{% load ui_tags %}{% ui_button label='Add product' url_name='control_room:product_create' %}"
        )
        html = template.render(Context())
        self.assertIn("<a ", html)
        self.assertIn('href="', html)
        self.assertIn("Add product", html)

    def test_submit_stays_button(self):
        template = Template("{% load ui_tags %}{% ui_button label='Save' type='submit' %}")
        html = template.render(Context())
        self.assertIn('type="submit"', html)
        self.assertNotIn("<a ", html)
