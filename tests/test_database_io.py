"""Validate JSON loading without modifying the real database."""

import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from petroflash.database import ComponentDatabase
from petroflash.properties import DataKind
from sample_data import methane


class TestDatabaseIO(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "components.json"

    def document(self):
        return {
            "schema_version": 1,
            "dataset_version": "test-1",
            "description": "Temporary loader test dataset",
            "components": [asdict(methane())],
        }

    def write_document(self, document):
        self.path.write_text(
            json.dumps(document, allow_nan=False),
            encoding="utf-8-sig",
        )

    def test_load_preserves_records_and_metadata(self):
        self.write_document(self.document())
        db = ComponentDatabase.from_file(self.path)
        component = db.get("74-82-8")

        self.assertEqual(db.dataset_version, "test-1")
        self.assertEqual(len(db), 1)
        self.assertEqual(component, methane())
        self.assertIs(
            component.critical_temperature.data_kind,
            DataKind.EVALUATED,
        )
        self.assertIsNone(component.critical_temperature.uncertainty)

    def test_rejects_unsupported_schema(self):
        for schema in (2, True, "1"):
            with self.subTest(schema=schema):
                document = self.document()
                document["schema_version"] = schema
                self.write_document(document)
                with self.assertRaises(ValueError):
                    ComponentDatabase.from_file(self.path)

    def test_revalidates_property_records(self):
        cases = (
            ("unit", "bar"),
            ("value", -1.0),
            ("data_kind", "unknown"),
            ("unexpected_field", 123),
        )
        for field, value in cases:
            with self.subTest(field=field):
                document = self.document()
                record = document["components"][0]["critical_pressure"]
                record[field] = value
                self.write_document(document)
                with self.assertRaises(ValueError):
                    ComponentDatabase.from_file(self.path)

    def test_rejects_duplicate_json_keys(self):
        text = json.dumps(self.document())
        text = text.replace(
            '"schema_version": 1',
            '"schema_version": 1, "schema_version": 1',
            1,
        )
        self.path.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            ComponentDatabase.from_file(self.path)

    def test_rejects_duplicate_components(self):
        document = self.document()
        document["components"].append(asdict(methane()))
        self.write_document(document)
        with self.assertRaisesRegex(ValueError, "Duplicate CAS"):
            ComponentDatabase.from_file(self.path)

    def test_rejects_nan_in_json(self):
        document = self.document()
        document["components"][0]["critical_pressure"]["value"] = float("nan")
        # Deliberately write invalid input to test the loader.
        self.path.write_text(
            json.dumps(document, allow_nan=True),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "Invalid JSON numeric"):
            ComponentDatabase.from_file(self.path)


if __name__ == "__main__":
    unittest.main()
