import json
from collections.abc import Collection
from abc import abstractmethod, ABCMeta
from typing import Optional, Tuple, Mapping

from ausweiskopie.editor.exporter import FieldLocation
from ausweiskopie.redact import Location, FieldDefinition


class BaseImporter(metaclass=ABCMeta):
    """ Generic base class to handle importing layouts """
    @abstractmethod
    def import_layout(self,
                      data: str) -> Collection[FieldLocation]:
        """
        Takes the given string data and converts it into FieldLocation objects.
        :param data: Any string data to be parsed
        :return:
        """
        pass

    @property
    @abstractmethod
    def supported_file_extensions(self) -> list[Tuple[str, str]]:
        """
        Returns a list of supported file extensions.
        The tuple to provide shall contain a label and a file extension glob.
        :return:
        """
        pass

    @property
    @abstractmethod
    def default_file_extension(self) -> str:
        """
        Returns the default file extension to use (`.xyz`)
        :return:
        """
        pass

    @property
    @abstractmethod
    def label(self) -> str:
        """
        Returns the translation key providing the name of the file format
        :return:
        """
        pass


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

    @property
    def supported_file_extensions(self):
        return [
            ("JSON Document", "*.json"),
        ]

    @property
    def default_file_extension(self):
        return ".json"

    @property
    def label(self):
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
