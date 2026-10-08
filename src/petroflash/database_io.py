"""Read the central component dataset and reconstruct validated objects."""

import json
from pathlib import Path

from .components import Component
from .properties import DataKind, PropertyRecord


PROPERTY_FIELDS = (
    "critical_temperature",
    "critical_pressure",
    "acentric_factor",
    "molar_mass",
)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError(f"Invalid JSON numeric constant: {value}")


def read_components(path):
    text = Path(path).read_text(encoding="utf-8-sig")
    document = json.loads(
        text,
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )

    expected = {
        "schema_version", "dataset_version", "description", "components"
    }
    if not isinstance(document, dict) or set(document) != expected:
        raise ValueError("Invalid dataset fields.")

    if (
        type(document["schema_version"]) is not int
        or document["schema_version"] != 1
    ):
        raise ValueError("Only schema_version 1 is supported.")

    for field in ("dataset_version", "description"):
        value = document[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string.")

    rows = document["components"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("components must be a non-empty list.")

    components = []

    for position, row in enumerate(rows):
        try:
            if not isinstance(row, dict):
                raise TypeError("Each component must be an object.")

            fields = dict(row)

            for name in PROPERTY_FIELDS:
                raw_record = fields[name]
                if not isinstance(raw_record, dict):
                    raise TypeError(f"{name} must be an object.")

                record = dict(raw_record)
                record["data_kind"] = DataKind(record["data_kind"])
                fields[name] = PropertyRecord(**record)

            components.append(Component(**fields))

        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"Invalid component at index {position}: {error}"
            ) from error

    return document["dataset_version"], tuple(components)
