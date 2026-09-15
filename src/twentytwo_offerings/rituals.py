from __future__ import annotations

import collections
import dataclasses
import enum
import itertools
import typing

from twentytwo_offerings.deck import (
    MajorArcana,
    MajorArcanaRank,
    MinorArcana,
    MinorArcanaRank,
    MinorArcanaSuit,
)
from twentytwo_offerings.lib import HAND_DATA
from twentytwo_offerings.ui import Glyphs

if typing.TYPE_CHECKING:
    from twentytwo_offerings.main import Altar, GameState


FIGURES = frozenset(
    {
        MinorArcanaRank.ACE,
        MinorArcanaRank.PAGE,
        MinorArcanaRank.KNIGHT,
        MinorArcanaRank.QUEEN,
        MinorArcanaRank.KING,
    }
)


NUMBERED = frozenset(rank for rank in MinorArcanaRank if rank not in FIGURES)


class OfferingType(enum.StrEnum):
    AT_ONCE_AUTOMATIC = enum.auto()
    AT_ONCE_MANUAL = enum.auto()
    ONE_BY_ONE = enum.auto()
    PROHIBITED = Glyphs.PROHIBITED


class RitualState(enum.StrEnum):
    COMPLETED = enum.auto()
    EMPTY = enum.auto()
    INVALID = enum.auto()
    LOCKED = enum.auto()  # LOCKED is PARTIAL for "at once" rituals
    READY = enum.auto()  # User  must select what to do to complete the ritual
    PARTIAL = enum.auto()


BAD_RITUAL_STATES = (
    RitualState.COMPLETED,
    RitualState.LOCKED,
    RitualState.INVALID,
)


class StateGetter(typing.Protocol):
    def __call__(
        self,
        altar_index: int,
        game_state: GameState,
    ) -> RitualState: ...


class OfferingClassifier(typing.Protocol):
    def __call__(
        self,
        altar_index: int,
        game_state: GameState,
    ) -> tuple[OfferingType, MajorArcana]: ...


@dataclasses.dataclass(frozen=True)
class Ritual:
    description: str
    get_offering_type: OfferingClassifier
    get_state: StateGetter


def at_once_automatic(
    altar_index: int,
    game_state: GameState,
) -> tuple[OfferingType, MajorArcana]:
    altar = game_state.altars[altar_index]

    if altar is None:
        raise RuntimeError(f"Altar#{altar_index} is expected to not be None!")

    return OfferingType.AT_ONCE_AUTOMATIC, altar.arcana_card


def at_once_manual(
    altar_index: int,
    game_state: GameState,
) -> tuple[OfferingType, MajorArcana]:
    altar = game_state.altars[altar_index]

    if altar is None:
        raise RuntimeError(f"Altar#{altar_index} is expected to not be None!")

    return OfferingType.AT_ONCE_MANUAL, altar.arcana_card


def one_by_one(
    altar_index: int,
    game_state: GameState,
) -> tuple[OfferingType, MajorArcana]:
    altar = game_state.altars[altar_index]

    if altar is None:
        raise RuntimeError(f"Altar#{altar_index} is expected to not be None!")

    return OfferingType.ONE_BY_ONE, altar.arcana_card


def fool_offering_type(
    altar_index: int,
    game_state: GameState,
) -> tuple[OfferingType, MajorArcana]:
    altar = game_state.altars[altar_index]

    if altar is None:
        raise RuntimeError(f"Altar#{altar_index} is expected to not be None!")

    for honored_altar in game_state.honored_pile:
        rank = honored_altar.arcana_card.rank
        if rank is MajorArcanaRank.DEVIL:
            continue

        # altar is being build
        altar.offering_type = honored_altar.offering_type
        altar.offering_src = honored_altar.arcana_card

        altar.state = altar.card_data.ritual.get_state(
            altar_index=altar_index,
            game_state=game_state,
        )

        return honored_altar.offering_type, honored_altar.arcana_card

    return OfferingType.PROHIBITED, altar.arcana_card


def get_state_verifier(
    rank: MajorArcanaRank,
    altar_index: int,
    game_state: GameState,
) -> Altar:
    altar = game_state.altars[altar_index]

    if altar is None:
        raise RuntimeError(
            f"Altar#{altar_index} is expected to have the {str(rank)} card!"
        )

    return altar


def chariot_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.CHARIOT,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    figures = 0
    numbered = 0
    for offering in altar.offerings:
        if offering.suit is not MinorArcanaSuit.SWORDS:
            return RitualState.INVALID

        if offering.rank in FIGURES:
            figures += 1
        else:
            numbered += 1

        if figures == 1 and numbered == 2:
            return RitualState.COMPLETED

        if figures > 1 or numbered > 2:
            return RitualState.INVALID

    return RitualState.PARTIAL


def death_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.DEATH,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(game_state.discard_pile) < 2:
        return RitualState.INVALID

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    pairs: list[tuple[MinorArcana, MinorArcana]] = []
    for card in game_state.discard_pile:
        for offering in game_state.hand:
            if offering is None:
                continue
            if card.rank == offering.rank:
                pairs.append((offering, card))

    if len(pairs) < 2:
        return RitualState.INVALID

    choices: list[
        tuple[tuple[MinorArcana, MinorArcana], tuple[MinorArcana, MinorArcana]]
    ] = [
        (pair_a, pair_b)
        for pair_a, pair_b in itertools.combinations(pairs, 2)
        if pair_a[0] is not pair_b[0] and pair_a[1] is not pair_b[1]
    ]

    match len(choices):
        case 0:
            return RitualState.INVALID
        case 1:
            return RitualState.LOCKED
        case _:
            return RitualState.READY


def devil_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.DEVIL,
        altar_index=altar_index,
        game_state=game_state,
    )

    if altar.state is RitualState.COMPLETED:
        return altar.state

    if any(card is None for card in game_state.hand[: HAND_DATA.slots // 2]):
        return RitualState.INVALID

    match len(altar.offerings):
        case 0:
            return RitualState.EMPTY
        case x if x < HAND_DATA.slots // 2:
            return RitualState.LOCKED
        case x if x == HAND_DATA.slots // 2:
            return RitualState.COMPLETED
        case _:
            return RitualState.INVALID


def emperor_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.EMPEROR,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    count = 0
    for offering in altar.offerings:
        if offering.rank is not MinorArcanaRank.KING:
            return RitualState.INVALID

        count += 1
        if count == 2:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def empress_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.EMPRESS,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    count = 0
    for offering in altar.offerings:
        if offering.rank is not MinorArcanaRank.QUEEN:
            return RitualState.INVALID

        count += 1
        if count == 2:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def fool_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.FOOL,
        altar_index=altar_index,
        game_state=game_state,
    )

    for honored_altar in game_state.honored_pile:
        rank = honored_altar.arcana_card.rank
        if rank is MajorArcanaRank.DEVIL:
            continue

        return RITUALS[rank].get_state(
            altar_index=altar_index,
            game_state=game_state,
        )

    if altar.offerings:
        return RitualState.INVALID
    else:
        return RitualState.EMPTY


def hanged_man_get_state(
    altar_index: int,
    game_state: GameState,
) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.HANGED_MAN,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    sixes = 0
    nines = 0
    for offering in altar.offerings:
        match offering.rank:
            case MinorArcanaRank.SIX:
                sixes += 1
                if sixes > 1:
                    return RitualState.INVALID
            case MinorArcanaRank.NINE:
                nines += 1
                if nines > 1:
                    return RitualState.INVALID
            case _:
                return RitualState.INVALID

        if sixes and nines:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def hermit_get_state(
    altar_index: int,
    game_state: GameState,
) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.HERMIT,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    offering = altar.offerings[0]
    if offering.suit is MinorArcanaSuit.WANDS and int(offering.rank) >= 9:
        return RitualState.COMPLETED
    else:
        return RitualState.INVALID


def hierophant_get_state(
    altar_index: int,
    game_state: GameState,
) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.HIEROPHANT,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    count = 0
    for offering in altar.offerings:
        if offering.suit is not MinorArcanaSuit.WANDS:
            return RitualState.INVALID

        count += 1

        if count >= 3:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def high_priestess_get_state(
    altar_index: int,
    game_state: GameState,
) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.HIGH_PRIESTESS,
        altar_index=altar_index,
        game_state=game_state,
    )

    half = HAND_DATA.slots // 2
    required_offerings_indexes = (0, half - 1, half, HAND_DATA.slots - 1)
    useable_hand_slots = sum(
        1
        for index in required_offerings_indexes
        if game_state.hand[index] is not None
    )

    if useable_hand_slots != len(required_offerings_indexes):
        return RitualState.INVALID

    match len(altar.offerings):
        case 0:
            return RitualState.EMPTY
        case 1 | 2 | 3:
            return RitualState.LOCKED
        case 4:
            return RitualState.COMPLETED
        case _:
            return RitualState.INVALID


def judgement_get_state(
    altar_index: int,
    game_state: GameState,
) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.JUDGEMENT,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    suits_count: collections.Counter[MinorArcanaSuit] = collections.Counter()
    for offering in altar.offerings:
        suits_count[offering.suit] += 1
        if suits_count[offering.suit] > 1:
            return RitualState.INVALID

    if len(suits_count) < 3:
        return RitualState.PARTIAL

    suit_matching_with_discarded: set[MinorArcanaSuit] = set()
    for discarded in game_state.discard_pile:
        if discarded.suit in suit_matching_with_discarded:
            continue

        if discarded.suit in suits_count:
            suit_matching_with_discarded.add(discarded.suit)
            if len(suit_matching_with_discarded) == 3:
                return RitualState.COMPLETED

    return RitualState.PARTIAL


def justice_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.JUSTICE,
        altar_index=altar_index,
        game_state=game_state,
    )

    if not altar.offerings:
        return RitualState.EMPTY

    coins: set[MinorArcanaRank] = set()
    swords: set[MinorArcanaRank] = set()
    for offering in altar.offerings:
        match offering.suit:
            case MinorArcanaSuit.COINS:
                coins.add(offering.rank)
            case MinorArcanaSuit.SWORDS:
                swords.add(offering.rank)
            case _:
                return RitualState.INVALID

        if coins & swords:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def lovers_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.LOVERS,
        altar_index=altar_index,
        game_state=game_state,
    )

    if not altar.offerings:
        return RitualState.EMPTY

    suits: set[MinorArcanaSuit] = set()
    for index, offering in enumerate(altar.offerings, start=1):
        if offering.rank not in FIGURES:
            return RitualState.INVALID

        if len(suits) != index:
            return RitualState.INVALID

        if len(suits) > 1:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def magician_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.LOVERS,
        altar_index=altar_index,
        game_state=game_state,
    )

    if not altar.offerings:
        return RitualState.EMPTY

    for _, offerings in itertools.groupby(
        altar.offerings,
        key=lambda offering: offering.rank,
    ):
        if len(tuple(offerings)) >= 3:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def moon_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.MOON,
        altar_index=altar_index,
        game_state=game_state,
    )

    half = HAND_DATA.slots // 2
    required_offerings_indexes = (altar_index, altar_index + half)
    useable_hand_slots = sum(
        1
        for index in required_offerings_indexes
        if game_state.hand[index] is not None
    )

    if useable_hand_slots != len(required_offerings_indexes):
        return RitualState.INVALID

    match len(altar.offerings):
        case 0:
            return RitualState.EMPTY
        case 1:
            return RitualState.LOCKED
        case 2:
            return RitualState.COMPLETED
        case _:
            return RitualState.INVALID


def star_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.STAR,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    total = 0
    for offering in altar.offerings:
        if (
            offering.suit is not MinorArcanaSuit.CUPS
            or offering.rank in FIGURES
        ):
            return RitualState.INVALID

        total += int(offering.rank)
        if total >= 17:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def strength_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.STRENGTH,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    count = 0
    for offering in altar.offerings:
        if offering.rank is not MinorArcanaRank.KNIGHT:
            return RitualState.INVALID

        count += 1
        if count == 2:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def sun_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.SUN,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    total = 0
    for offering in altar.offerings:
        if (
            offering.suit is not MinorArcanaSuit.COINS
            or offering.rank in FIGURES
        ):
            return RitualState.INVALID

        total += int(offering.rank)
        if total >= 19:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def temperance_get_state(
    altar_index: int,
    game_state: GameState,
) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.TEMPERANCE,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    ordered = sorted(altar.offerings, key=lambda offering: int(offering.rank))
    for next_card_index, offering in enumerate(ordered[:-1], start=1):
        if offering.suit is not MinorArcanaSuit.CUPS:
            return RitualState.INVALID

        delta = int(ordered[next_card_index].rank) - int(offering.rank)
        if delta == 1:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def tower_get_state(
    altar_index: int,
    game_state: GameState,
) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.TEMPERANCE,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    ordered = sorted(altar.offerings, key=lambda offering: int(offering.rank))
    consecutive_deltas = 0
    for next_card_index, offering in enumerate(ordered[:-1], start=1):
        if offering.rank in FIGURES:
            return RitualState.INVALID

        delta = int(ordered[next_card_index].rank) - int(offering.rank)
        match delta:
            case 0:
                continue
            case 1:
                consecutive_deltas += 1
            case _:
                consecutive_deltas = 0

        if consecutive_deltas == 3:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


def wheel_of_fortune_get_state(
    altar_index: int,
    game_state: GameState,
) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.WHEEL_OF_FORTUNE,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(game_state.discard_pile) < 3:
        return RitualState.INVALID

    match len(altar.offerings):
        case 0:
            return RitualState.EMPTY
        case 1 | 2:
            return RitualState.LOCKED
        case 3:
            return RitualState.COMPLETED
        case _:
            return RitualState.INVALID


def world_get_state(altar_index: int, game_state: GameState) -> RitualState:
    altar = get_state_verifier(
        rank=MajorArcanaRank.WORLD,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(altar.offerings) == 0:
        return RitualState.EMPTY

    suits: set[MinorArcanaSuit] = set()
    for index, offering in enumerate(altar.offerings, start=1):
        suits.add(offering.suit)

        if len(suits) != index:
            return RitualState.INVALID

        if len(suits) == 4:
            return RitualState.COMPLETED

    return RitualState.PARTIAL


RITUALS: dict[MajorArcanaRank, Ritual] = {
    MajorArcanaRank.FOOL: Ritual(
        description=(
            "The same condition as the last arcana you honored,"
            " [underline]except Devil[/underline]."
        ),
        get_offering_type=fool_offering_type,
        get_state=fool_get_state,
    ),
    MajorArcanaRank.MAGICIAN: Ritual(
        description="3 of a kind.",
        get_offering_type=one_by_one,
        get_state=magician_get_state,
    ),
    MajorArcanaRank.HIGH_PRIESTESS: Ritual(
        description=(
            "The 2 cards of the left column of your hand"
            " and the 2 cards of the right of your hand,"
            " [underline]at once[/underline]."
        ),
        get_offering_type=at_once_manual,
        get_state=high_priestess_get_state,
    ),
    MajorArcanaRank.EMPRESS: Ritual(
        description=f"2 Queens ({MinorArcanaRank.QUEEN!s}).",
        get_offering_type=one_by_one,
        get_state=empress_get_state,
    ),
    MajorArcanaRank.EMPEROR: Ritual(
        description=f"2 Kings ({MinorArcanaRank.KING!s}).",
        get_offering_type=one_by_one,
        get_state=emperor_get_state,
    ),
    MajorArcanaRank.HIEROPHANT: Ritual(
        description=f"Any 3 {MinorArcanaSuit.WANDS!s} cards.",
        get_offering_type=one_by_one,
        get_state=hierophant_get_state,
    ),
    MajorArcanaRank.LOVERS: Ritual(
        description="2 figures of different suits.",
        get_offering_type=one_by_one,
        get_state=lovers_get_state,
    ),
    MajorArcanaRank.CHARIOT: Ritual(
        description=f"3 {MinorArcanaSuit.SWORDS!s} cards, 1 must be a figure.",
        get_offering_type=one_by_one,
        get_state=chariot_get_state,
    ),
    MajorArcanaRank.JUSTICE: Ritual(
        description=(
            f"1 {MinorArcanaSuit.SWORDS!s} and 1 {MinorArcanaSuit.COINS!s}"
            f" cards of the same value."
        ),
        get_offering_type=one_by_one,
        get_state=justice_get_state,
    ),
    MajorArcanaRank.HERMIT: Ritual(
        description=(
            f"Single {MinorArcanaSuit.WANDS!s} card that is 9 or higher,"
            f" including figures."
        ),
        get_offering_type=one_by_one,
        get_state=hermit_get_state,
    ),
    MajorArcanaRank.WHEEL_OF_FORTUNE: Ritual(
        description=(
            "Shuffle your Hand, use 3 cards to honor the Wheel of Fortune card."
            " Shuffle the Discard Pile, put 3 cards from the Discard Pile into"
            " your Hand."
        ),
        get_offering_type=at_once_manual,
        get_state=wheel_of_fortune_get_state,
    ),
    MajorArcanaRank.STRENGTH: Ritual(
        description=f"2 Knights ({MinorArcanaRank.KNIGHT!s}).",
        get_offering_type=one_by_one,
        get_state=strength_get_state,
    ),
    MajorArcanaRank.HANGED_MAN: Ritual(
        description=(
            f"A {MinorArcanaRank.SIX!s} and a {MinorArcanaRank.NINE!s}."
        ),
        get_offering_type=one_by_one,
        get_state=hanged_man_get_state,
    ),
    MajorArcanaRank.DEATH: Ritual(
        description=(
            "2 cards from your hand and 2 cards from your Discard Pile"
            " that have the same values as those 2 cards from your Hand,"
            " [underline]at once[/underline]."
        ),
        get_offering_type=at_once_manual,
        get_state=death_get_state,
    ),
    MajorArcanaRank.TEMPERANCE: Ritual(
        description=f"2 {MinorArcanaSuit.CUPS!s} cards of consecutive value.",
        get_offering_type=one_by_one,
        get_state=temperance_get_state,
    ),
    MajorArcanaRank.DEVIL: Ritual(
        description=(
            "When the Devil appears, send the top row of your Hand to the"
            " Discard Pile. Devil is always honored and can't be sent back"
            " to the Arcana Pile."
        ),
        get_offering_type=at_once_automatic,
        get_state=devil_get_state,
    ),
    MajorArcanaRank.TOWER: Ritual(
        description="4 numbered consecutive cards.",
        get_offering_type=one_by_one,
        get_state=tower_get_state,
    ),
    MajorArcanaRank.STAR: Ritual(
        description=(
            f"Numbered {MinorArcanaSuit.CUPS!s} cards that adds at least 17."
        ),
        get_offering_type=one_by_one,
        get_state=star_get_state,
    ),
    MajorArcanaRank.MOON: Ritual(
        description=(
            "The 2 cards on the Hand column below the Arcana,"
            " [underline]at once[/underline]."
        ),
        get_offering_type=at_once_manual,
        get_state=moon_get_state,
    ),
    MajorArcanaRank.SUN: Ritual(
        description=(
            f"Numbered {MinorArcanaSuit.COINS!s} cards that add at least 19."
        ),
        get_offering_type=one_by_one,
        get_state=sun_get_state,
    ),
    MajorArcanaRank.JUDGEMENT: Ritual(
        description=(
            "Any 3 cards of different suits. Choose 3 cards of the same suits"
            " from the Discard Pile and put them back to the Offerings Pile,"
            " then reshuffle the Offerings Pile."
        ),
        get_offering_type=one_by_one,
        get_state=judgement_get_state,
    ),
    MajorArcanaRank.WORLD: Ritual(
        description="1 card of each suit.",
        get_offering_type=one_by_one,
        get_state=world_get_state,
    ),
}
