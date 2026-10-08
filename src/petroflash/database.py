"""In-memory component lookup with explicit identity checks."""

import re
from collections.abc import Iterable

from .components import Component


def validate_cas_number(cas_number: str) -> None:
    """Check CAS syntax and checksum, not chemical identity."""

    if not isinstance(cas_number, str):
        raise TypeError("CAS number must be a string.")

    if re.fullmatch(r"[1-9][0-9]{1,6}-[0-9]{2}-[0-9]", cas_number) is None:
        raise ValueError(f"Invalid CAS format: {cas_number!r}")

    digits = cas_number.replace("-", "")
    total = sum(
        position * int(digit)
        for position, digit in enumerate(reversed(digits[:-1]), start=1)
    )

    if total % 10 != int(digits[-1]):
        raise ValueError(f"Invalid CAS check digit: {cas_number!r}")


def _lookup_key(identifier: str) -> str:
    if not isinstance(identifier, str):
        raise TypeError("Component identifier must be a string.")
    key = identifier.strip().casefold()
    if not key:
        raise ValueError("Component identifier cannot be empty.")
    return key


class ComponentDatabase:
    """A collection indexed by exact component name and CAS number."""

    def __init__(self, components: Iterable[Component]):
        by_cas: dict[str, Component] = {}
        index: dict[str, Component] = {}

        for component in components:
            if not isinstance(component, Component):
                raise TypeError("Database entries must be Component objects.")

            validate_cas_number(component.cas_number)

            if component.cas_number in by_cas:
                raise ValueError(
                    f"Duplicate CAS number: {component.cas_number}"
                )

            keys = {
                _lookup_key(component.name),
                _lookup_key(component.cas_number),
            }

            for key in keys:
                if key in index:
                    raise ValueError(f"Ambiguous component identifier: {key!r}")

            by_cas[component.cas_number] = component
            for key in keys:
                index[key] = component

        self._by_cas = by_cas
        self._index = index

    def __len__(self) -> int:
        return len(self._by_cas)

    def names(self) -> tuple[str, ...]:
        return tuple(component.name for component in self._by_cas.values())

    def get(self, identifier: str) -> Component:
        key = _lookup_key(identifier)
        try:
            return self._index[key]
        except KeyError:
            raise KeyError(f"Component not found: {identifier!r}") from None

    def select(self, identifiers: Iterable[str]) -> tuple[Component, ...]:
        if isinstance(identifiers, (str, bytes)):
            raise TypeError("Pass a collection of identifiers, not one string.")

        selected = tuple(self.get(identifier) for identifier in identifiers)

        if not selected:
            raise ValueError("Select at least one component.")

        cas_numbers = [component.cas_number for component in selected]
        if len(cas_numbers) != len(set(cas_numbers)):
            raise ValueError("The same component was selected more than once.")

        return selected

    @classmethod
    def from_file(cls, path):
        """Load the central dataset and validate its component index."""
        from .database_io import read_components

        dataset_version, components = read_components(path)
        database = cls(components)
        database.dataset_version = dataset_version
        return database
