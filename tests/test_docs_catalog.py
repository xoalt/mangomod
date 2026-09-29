"""The pinned Mango reference stays covered without dropping older options."""

import re
import unittest
from pathlib import Path

from mangomod.mango_schema import DISPATCHERS, DOCUMENTED_NO_ATTRIBUTES, no_attributes_confirmed
from mangomod.mango_settings import SETTINGS


DOCS = Path(__file__).resolve().parents[1] / "docs" / "upstream-mango"
SCALAR_PAGES = (
    "configuration/input.md",
    "configuration/miscellaneous.md",
    "visuals/animations.md",
    "visuals/effects.md",
    "visuals/theming.md",
    "window-management/layouts.md",
    "window-management/overview.md",
)


def table_keys(path):
    return set(re.findall(r"^\| `([a-z][a-z0-9_]*)` \|", path.read_text(), re.M))


class DocsCatalogTests(unittest.TestCase):
    def test_documented_scalar_options_are_reachable(self):
        available = {item["key"] for item in SETTINGS}
        for page in SCALAR_PAGES:
            with self.subTest(page=page):
                self.assertFalse(table_keys(DOCS / page) - available)

    def test_documented_dispatchers_are_in_action_library(self):
        available = {item["cmd"] for group in DISPATCHERS.values() for item in group}
        self.assertFalse(table_keys(DOCS / "bindings/keys.md") - available)

    def test_no_attribute_claims_have_explicit_documentation(self):
        source = (DOCS / 'bindings/keys.md').read_text()
        documented = set(re.findall(r'^\|\s*`(\w+)`\s*\|\s*-\s*\|', source, re.M))
        self.assertEqual(DOCUMENTED_NO_ATTRIBUTES, documented)
        self.assertTrue(no_attributes_confirmed('togglefloating'))
        self.assertFalse(no_attributes_confirmed('viewprev_have_client'))
        self.assertFalse(no_attributes_confirmed('future_command'))


if __name__ == "__main__":
    unittest.main()
