import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LocaleCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = (ROOT / "web/messages.js").read_text(encoding="utf-8")
        cls.catalog = json.loads(source.removeprefix("const messages = ").strip().removesuffix(";"))

    def test_locales_match_readmes(self):
        translations = (ROOT / "docs/readme").glob("README.*.md")
        expected = {"en"} | {path.name.split(".")[1] for path in translations}
        self.assertEqual(self.catalog.keys(), expected)

    def test_all_translations_keep_template_fields(self):
        english = self.catalog["en"]
        for language, messages in self.catalog.items():
            with self.subTest(language=language):
                self.assertEqual(messages.keys(), english.keys())
                for key, text in messages.items():
                    self.assertTrue(text.strip(), key)
                    self.assertCountEqual(re.findall(r"{\w+}", text), re.findall(r"{\w+}", english[key]), key)

    def test_referenced_messages_exist(self):
        html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        keys = set(re.findall(r'data-i18n(?:-aria|-placeholder)?="(\w+)"', html))
        for name in ("app.js", "language.js"):
            code = (ROOT / "web" / name).read_text(encoding="utf-8")
            keys.update(re.findall(r'\bt\("(\w+)"', code))
        self.assertFalse(keys - self.catalog["en"].keys())
