"""Contains the field definitions of various travel documents."""

from .definitions import FieldDefinition, Field, Location

## New German identity card

# Issued from 2010 to 2019
FIELDS_NPA_FRONT_2010: FieldDefinition = {
    Field.DOCUMENT_NUMBER: (
        Location((0.6907, 0.0402), (0.9661, 0.1230)),
    ),
    Field.PHOTO: (
        Location((0.0311, 0.1867), (0.4237, 0.9821)),
    ),
    Field.CAN: (
        Location((0.7528, .64210), (0.9548, 0.7527)),
    ),
    Field.SIGNATURE: (
        Location((0.4379, 0.8000), (0.8757, 0.9933)),
    ),
    Field.SURNAME: (
        Location((0.4528, 0.1530), (0.9915, 0.2179)),
    ),
    Field.GIVEN_NAME: (
        Location((0.4528, 0.3199), (0.9915, 0.3740)),
    ),
    Field.DATE_OF_BIRTH: (
        Location((0.4528, 0.4482), (0.6660, 0.5146)),
    ),
    Field.NATIONALITY: (
        Location((0.6660, 0.4482), (0.9915, 0.5146)),
    ),
    Field.PLACE_OF_BIRTH: (
        Location((0.4528, 0.5593), (0.9915, 0.6209)),
    ),
    Field.NAME_AT_BIRTH: (
        Location((0.4528, 0.2179), (0.9915, 0.2797)),
    ),
    Field.DATE_OF_EXPIRY: (
        Location((0.4528, 0.6955), (0.6660, 0.7527)),
    )
}

# Issued from 2019-2021
FIELDS_NPA_FRONT_2019: FieldDefinition = {
    Field.DOCUMENT_NUMBER: (
        Location((0.6907, 0.0402), (0.9661, 0.1230)),
    ),
    Field.PHOTO: (
        Location((0.0311, 0.1867), (0.4237, 0.9821)),
    ),
    Field.CAN: (
        Location((0.7528, .64210), (0.9548, 0.7527)),
    ),
    Field.SIGNATURE: (
        Location((0.44, 0.8000), (0.8757, 0.9933)),
    ),
    Field.SURNAME: (
        Location((0.4600, 0.1530+0.0352), (0.9915, 0.2179+0.0352)),
    ),
    Field.GIVEN_NAME: (
        Location((0.44, 0.3364), (0.9915, 0.4117)),
    ),
    Field.DATE_OF_BIRTH: (
        Location((0.44, 0.4705), (0.6660, 0.5388)),
    ),
    Field.NATIONALITY: (
        Location((0.6660, 0.4705), (0.9915, 0.5388)),
    ),
    Field.PLACE_OF_BIRTH: (
        Location((0.44, 0.5593), (0.9915, .6282)),
    ),
    Field.NAME_AT_BIRTH: (
        Location((0.4600, 0.2179+0.0352), (0.9915, 0.2797+0.0352)),
    ),
    Field.DATE_OF_EXPIRY: (
        Location((0.44, 0.6955), (0.6660, 0.7527)),
    )
}


# Issued since 2021
FIELDS_NPA_FRONT_2021: FieldDefinition = {
    Field.DOCUMENT_NUMBER: (
        Location((0.6907, 0.0402), (0.9661, 0.1230)),
    ),
    Field.PHOTO: (
        Location((0.0311, 0.1867), (0.4237, 0.9821)),
    ),
    Field.CAN: (
        Location((0.7528, 0.7383), (0.9548, 0.8345)),
    ),
    Field.SIGNATURE: (
        Location((0.4379, 0.8322), (0.8757, 0.9933)),
    ),
    Field.SURNAME: (
        Location((0.4576, 0.2483), (0.9915, 0.3199)),
    ),
    Field.GIVEN_NAME: (
        Location((0.4379, 0.4139), (0.9915, 0.4855)),
    ),
    Field.DATE_OF_BIRTH: (
        Location((0.4379, 0.5593), (0.6511, 0.6209)),
    ),
    Field.NATIONALITY: (
        Location((0.6596, 0.5593), (0.9237, 0.6209)),
    ),
    Field.PLACE_OF_BIRTH: (
        Location((0.4379, 0.6398), (0.9915, 0.7114)),
    ),
    Field.NAME_AT_BIRTH: (
        Location((0.4576, 0.3154), (0.9915, 0.387)),
    ),
    Field.DATE_OF_EXPIRY: (
        Location((0.4379, 0.78), (0.6511, 0.8322)),
    )
}

# The back of the electronic id card has not changed.
FIELDS_NPA_BACK: FieldDefinition = {
    Field.COLOUR_OF_EYES: (
        Location((0.0353, 0.0582), (0.3927, 0.1253)),
    ),
    Field.HEIGHT: (
        Location((0.0353, 0.1521), (0.2218, 0.2192)),
    ),
    Field.AUTHORITY: (
        Location((0.0353, 0.3557), (0.2966, 0.4228)),
    ),
    Field.ADDRESS: (
        Location((0.4449, 0.0582), (0.9435, 0.311)),
    ),
    Field.RELIGIOUS_NAME_OR_PSEUDONYM: (
        Location((0.4449, 0.3803), (0.8955, 0.4474)),
    ),
    Field.DOCUMENT_NUMBER: (
        Location((0.2684, 0.5235), (0.4393, 0.5817)),
        Location((0.2006, 0.6711), (0.5028, 0.745)),
    ),
    Field.MACHINE_READABLE_ZONE: (
        Location((0.2684, 0.5235), (0.9562, 0.5817)),
        Location((0.0367, 0.6488), (0.9732, 0.9195)),
    ),
    Field.DATE_OF_BIRTH: (
        Location((0.0466, 0.745), (0.2359, 0.8233)),
    ),
    Field.DATE_OF_EXPIRY: (
        Location((0.291, 0.745), (0.4802, 0.8233)),
    ),
    Field.DATE: (
        Location((0.0353, 0.2438), (0.2359, 0.311)),
    ),
    Field.NATIONALITY: (
        Location((0.5028, 0.745), (0.6003, 0.8233)),
    ),
    Field.GIVEN_NAME: (
        Location((0.0494, 0.8233), (0.9633, 0.9016)),
        Location((0.4675, 0.5235), (0.9562, 0.5817)),
    )
}


## Temporary German id cards
FIELDS_VORLAEUFIG_FRONT: FieldDefinition = {
    Field.DOCUMENT_NUMBER: (
        Location((.7583, .18), (0.9664, 0.25)),
        Location((0.0400, 0.867), (0.2462, 0.93)),
    ),
    Field.PHOTO: (
        Location((0.0105, 0.05), (0.2733, .5525)),
    ),
    Field.SURNAME: (
        Location((0.2733, 0.18), (0.7530, 0.235)),
        Location((0.0400, 0.8040), (0.7795, 0.867)),
    ),
    Field.NAME_AT_BIRTH: (
        Location((0.2733, 0.235), (0.7530, 0.295)),
    ),
    Field.GIVEN_NAME: (
        Location((.2733, 0.3137), (0.9664, 0.370)),
        Location((0.0400, 0.8040), (0.7795, 0.867)),
    ),
    Field.DATE_OF_BIRTH: (
        Location((.2733, 0.3861), (0.4693, 0.445)),
        Location((0.3074, 0.867), (0.4503, 0.93)),
    ),
    Field.PLACE_OF_BIRTH: (
        Location((0.4693, 0.3861), (0.9664, 0.445)),
    ),
    Field.NATIONALITY: (
        Location((0.2773, 0.4575), (0.4816, 0.5125)),
        Location((0.2462, 0.867), (0.3074, 0.93)),
    ),
    Field.HEIGHT: (
        Location((0.5125, 0.4575), (0.6340, 0.5125)),
    ),
    Field.COLOUR_OF_EYES: (
        Location((0.6340, 0.4575), (0.8306, 0.5125)),
    ),
    Field.ADDRESS: (
        Location((0.2733, 0.5289), (0.9664, 0.5733)),
    ),
    Field.DATE: (
        Location((0.2733, 0.5956), (0.6163, 0.6428)),
    ),
    Field.DATE_OF_EXPIRY: (
        Location((0.6163, 0.5959), (0.9644, 0.6428)),
        Location((0.4714, 0.867), (0.6136, 0.93)),
    ),
    Field.SIGNATURE: (
        Location((0.2733, 0.666), (0.9644, 0.781)),
    ),
    Field.MACHINE_READABLE_ZONE: (
        Location((0.0400, 0.8040), (0.7795, 0.93)),
    ),
}

FIELDS_VORLAEUFIG_BACK: FieldDefinition = {
    Field.RELIGIOUS_NAME_OR_PSEUDONYM : (
        Location((0.0723, 0.225), (0.7830, 0.275)),
    ),
    Field.AUTHORITY: (
        Location((0.0723, 0.4875), (0.7830, 0.5525)),
    ),
}

## German passports
FIELDS_PASSPORT: FieldDefinition = {
    Field.DOCUMENT_NUMBER: (
        Location((0.6186, 0.1174), (0.7902, 0.1596)),
        Location((0.036, 0.8568), (0.25, 0.9216))
    ),
    Field.PHOTO: (
        Location((0.0254, 0.1747), (0.3029, 0.6777)),
    ),
    Field.SURNAME: (
        Location((0.3347, 0.1897), (0.7987, 0.2319)),
        Location((0.1440, 0.7921), (0.9597, 0.8568)),
    ),
    Field.NAME_AT_BIRTH: (
        Location((0.3347, 0.2319), (0.7987, 0.2741)),
    ),
    Field.GIVEN_NAME: (
        Location((0.3347, 0.2951), (0.7987, 0.3373)),
        Location((0.1440, 0.7921), (0.9597, 0.8568)),
    ),
    Field.DATE_OF_BIRTH: (
        Location((0.3347, 0.41), (0.475, 0.4638)),
        Location((0.9237, 0.3012), (0.9597, 0.4006)),
        Location((0.3114, 0.8568), (0.4576, 0.9216)),
    ),
    Field.SEX: (
        Location((0.5423, 0.41), (0.5699, 0.4638)),
        Location((0.4576, 0.8568), (0.4767, 0.9216)),
    ),
    Field.NATIONALITY: (
        Location((0.7012, 0.41), (0.9046, 0.4638)),
        Location((0.25, 0.8568), (0.3114, 0.9216)),
    ),
    Field.PLACE_OF_BIRTH: (
        Location((0.3347, 0.4789), (0.9046, 0.52108)),
    ),
    Field.DATE: (
        Location((0.3347, 0.5753), (0.5317, 0.6174)),
        Location((0.5974, 0.8568), (0.7033, 0.9216)),
    ),
    Field.DATE_OF_EXPIRY: (
        Location((0.5317, 0.5753), (0.7287, 0.6174)),
        Location((0.4767, 0.8568), (0.5974, 0.9216)),
    ),
    Field.AUTHORITY: (
        Location((0.3347, 0.6386), (0.7200, 0.6807)),
    ),
    Field.SIGNATURE: (
        Location((0.7309, 0.6024), (0.9851, 0.7469)),
    ),
    Field.MACHINE_READABLE_ZONE: (
        Location((0.036, 0.7921), (0.9597, 0.9216)),
    )
}


FIELDS_NO_BACK = {}