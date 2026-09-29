"""Ensure documented settings never fall back to English UI copy."""

import unittest

from mangomod.i18n import translate
from mangomod.mango_settings import SECTIONS, SETTINGS


class ArabicCatalogTests(unittest.TestCase):
    def test_catalog_titles_descriptions_and_sections_are_localized(self):
        for section in SECTIONS:
            self.assertNotEqual(translate(section, 'ar'), section, section)
        for option in SETTINGS:
            self.assertNotEqual(translate(option['label'], 'ar'), option['label'], option['key'])
            self.assertNotEqual(translate(option['desc'], 'ar'), option['desc'], option['key'])

    def test_code_values_remain_literal(self):
        for literal in ('spawn', 'SUPER+Return', 'borderpx', '0xf2a56bff'):
            self.assertEqual(translate(literal, 'ar'), literal)


if __name__ == '__main__':
    unittest.main()
