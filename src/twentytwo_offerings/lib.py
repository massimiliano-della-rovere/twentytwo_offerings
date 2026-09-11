import dataclasses


@dataclasses.dataclass(frozen=True)
class ContainerData:
    slots: int
    name: str
    content: str
    game_state_attribute_name: str


ALTARS_DATA = ContainerData(
    slots=4,
    name="altars",
    content="altar",
    game_state_attribute_name="altars",
)
HAND_DATA = ContainerData(
    slots=8,
    name="hand",
    content="offering",
    game_state_attribute_name="hand",
)


def hand_row_indexes_by_offering_index(offering_index: int) -> range:
    if offering_index < HAND_DATA.slots / 2:
        indexes = range(0, HAND_DATA.slots // 2)
    else:
        indexes = range(HAND_DATA.slots // 2, HAND_DATA.slots)

    return indexes


def hand_column_indexes_by_altar_index(altar_index: int) -> range:
    return range(altar_index, HAND_DATA.slots, ALTARS_DATA.slots)
