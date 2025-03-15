import json
from collections.abc import Collection
from typing import Optional, Any, Tuple, Mapping

from ausweiskopie.editor.exporter import FieldLocation
from ausweiskopie.redact import Location, Field, FieldDefinition


class BaseImporter:
    def import_layout(self,
                      data: str) -> Collection[FieldLocation]:
        raise NotImplementedError()

    @staticmethod
    def get_supported_file_extensions() -> list[Tuple[str, str]]:
        raise NotImplementedError()

    @staticmethod
    def get_default_file_extension() -> str:
        raise NotImplementedError()

    @staticmethod
    def get_import_label() -> str:
        raise NotImplementedError()


class BasicJsonImporter(BaseImporter):
    def import_layout(self,
                      data: str) -> Collection[FieldLocation]:
        parsed = json.loads(data)

        field_locations: list[FieldLocation] = []
        for field_name, locations in parsed.items():
            for raw_location in locations:
                field_locations.append(
                    FieldLocation(
                        field=field_name,
                        location=self._parse_location(raw_location),
                        rect_id=None
                    )
                )

        return field_locations

    @staticmethod
    def _parse_location(raw_location) -> Location:
        top_left = (raw_location['top_left'][0], raw_location['top_left'][1])
        bottom_right = (raw_location['bottom_right'][0], raw_location['bottom_right'][1])
        return Location(top_left, bottom_right)

    @staticmethod
    def get_supported_file_extensions():
        return [
            ("JSON Document", "*.json"),
        ]

    @staticmethod
    def get_default_file_extension():
        return ".json"

    @staticmethod
    def get_import_label():
        return "EDITOR_FORMAT_BASIC_JSON"


IMPORTERS: Mapping[str, BaseImporter] = {
    'json': BasicJsonImporter(),
}


def get_importer(importer_name: str) -> Optional[BaseImporter]:
    if importer_name not in IMPORTERS:
        return None

    return IMPORTERS[importer_name]


def import_from_field_definition(field_definition: FieldDefinition) -> Collection[FieldLocation]:
    field_locations = []

    for field, locations in field_definition.items():
        for location in locations:
            field_locations.append(FieldLocation(field=field, location=location, rect_id=None))

    return field_locations
