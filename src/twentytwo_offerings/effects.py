from __future__ import annotations

import collections
import itertools
import random
import typing

from twentytwo_offerings.deck import (
    MajorArcanaRank,
    MinorArcana,
    MinorArcanaSuit,
)
from twentytwo_offerings.lib import (
    HAND_DATA,
    hand_row_indexes_by_offering_index,
)
from twentytwo_offerings.rituals import RITUALS, OfferingType, RitualState
from twentytwo_offerings.ui import Glyphs, ask, output

if typing.TYPE_CHECKING:
    from twentytwo_offerings.main import Altar, GameState


class Effect(typing.Protocol):
    def __call__(
        self,
        altar_index: int,
        game_state: GameState,
        test_only: bool = False,
    ) -> bool: ...


def effect_verifier(
    rank: MajorArcanaRank,
    altar_index: int,
    game_state: GameState,
    allow_offerings: bool = False,
) -> Altar:
    altar = game_state.altars[altar_index]

    if altar is None:
        raise RuntimeError(
            f"Altar#{altar_index} is expected to have the {str(rank)} card!"
        )
    if not allow_offerings and altar.offerings:
        raise RuntimeError(
            (
                f"The {str(rank)} is an 'at once' card,"
                f" so no partial offerings are allowed!"
            )
        )

    return altar


def death_effect(
    altar_index: int,
    game_state: GameState,
    test_only: bool = False,
) -> bool:
    altar = effect_verifier(
        rank=MajorArcanaRank.DEATH,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(game_state.discard_pile) < 2:
        return False

    hand_set = frozenset(
        offering
        for offering in game_state.hand
        if isinstance(offering, MinorArcana)
    )

    if len(hand_set) < 2:
        return False

    choices_per_offering: collections.defaultdict[
        MinorArcana, list[MinorArcana]
    ] = collections.defaultdict(list)

    for offering in hand_set:
        for discarded in game_state.discard_pile:
            if offering.rank == discarded.rank:
                choices_per_offering[offering].append(discarded)

    if len(choices_per_offering) < 2:
        return False

    cards_sep = "+"
    multiple_choices_sep = "\n"

    try:
        lookup_table: dict[str, MinorArcana] = {}
        choices: dict[str, str] = {}
        for offering_a, offering_b in itertools.combinations(
            choices_per_offering, 2
        ):
            offering_a_str = str(offering_a)
            offering_b_str = str(offering_b)
            lookup_table[offering_a_str] = offering_a
            lookup_table[offering_b_str] = offering_b
            for discarded_a in choices_per_offering[offering_a]:
                discarded_a_str = str(discarded_a)
                lookup_table[discarded_a_str] = discarded_a
                for discarded_b in choices_per_offering[offering_b]:
                    discarded_b_str = str(discarded_b)
                    lookup_table[discarded_b_str] = discarded_b
                    if discarded_a is discarded_b:
                        continue

                    key = cards_sep.join(
                        (
                            offering_a_str,
                            offering_b_str,
                            discarded_a_str,
                            discarded_b_str,
                        )
                    )
                    text = (
                        f"{offering_a_str} {cards_sep} {offering_b_str}"
                        f" {Glyphs.ARROW_URDL}"
                        f" {discarded_a_str} {cards_sep} {discarded_b_str}"
                    )
                    choices[key] = text

        if len(choices) == 0:
            return False

        if test_only:
            return True

        if len(choices) == 1:
            chosen = next(iter(choices))
        else:
            chosen = ask(
                title="Death requirements",
                text=RITUALS[MajorArcanaRank.DEATH].description,
                choices=choices,
                choices_min=1,
                choices_max=1,
            )
        for quadruple in chosen.split(multiple_choices_sep):
            offering_a_str, offering_b_str, discarded_a_str, discarded_b_str = (
                quadruple.split(cards_sep)
            )

            offering_a = lookup_table[offering_a_str]
            offering_b = lookup_table[offering_b_str]
            discarded_a = lookup_table[discarded_a_str]
            discarded_b = lookup_table[discarded_b_str]

            index_offering_a = game_state.hand.index(offering_a)
            index_offering_b = game_state.hand.index(offering_b)
            game_state.hand[index_offering_a] = None
            game_state.hand[index_offering_b] = None

            game_state.discard_pile.remove(discarded_a)
            game_state.discard_pile.remove(discarded_b)

            altar.offerings.append(offering_a)
            altar.offerings.append(offering_b)
            altar.offerings.append(discarded_a)
            altar.offerings.append(discarded_b)

        altar.state = RitualState.COMPLETED
        return True
    except Exception as e:
        print(e)
        import pdb

        pdb.post_mortem()
        raise


def devil_effect(
    altar_index: int,
    game_state: GameState,
    test_only: bool = False,
) -> bool:
    altar = effect_verifier(
        rank=MajorArcanaRank.DEVIL,
        altar_index=altar_index,
        game_state=game_state,
    )

    offerings: list[MinorArcana] = []
    for hand_index in hand_row_indexes_by_offering_index(offering_index=0):
        if (offering := game_state.hand[hand_index]) is None:
            raise RuntimeError("Hand must not have gaps in this moment!")

        if test_only:
            continue

        game_state.hand[hand_index] = None
        game_state.discard_pile.appendleft(offering)
        offerings.append(offering)

    if test_only:
        return True

    from_hand = "[bright_black],[/bright_black] ".join(
        str(card) for card in offerings
    )
    output(
        title="Effects of the Ritual",
        text=f"Cards from the Hand: {from_hand}.",
    )

    altar.state = RitualState.COMPLETED
    return True


def fool_effect(
    altar_index: int,
    game_state: GameState,
    test_only: bool = False,
) -> bool:
    altar = effect_verifier(
        rank=MajorArcanaRank.FOOL,
        altar_index=altar_index,
        game_state=game_state,
    )

    if (
        altar.offering_src.rank is MajorArcanaRank.FOOL
        or altar.offering_type is OfferingType.PROHIBITED
    ):
        return False

    effect = EFFECTS[altar.offering_src.rank]
    if not callable(effect):
        return True

    return effect(
        altar_index=altar_index,
        game_state=game_state,
        test_only=test_only,
    )


def high_priestess_effect(
    altar_index: int,
    game_state: GameState,
    test_only: bool = False,
) -> bool:
    altar = effect_verifier(
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
        return False

    if test_only:
        return True

    for hand_index in required_offerings_indexes:
        offering = game_state.hand[hand_index]
        game_state.hand[hand_index] = None
        altar.offerings.append(offering)  # pyright: ignore[reportArgumentType]

    from_hand = "[bright_black],[/bright_black] ".join(
        str(card) for card in altar.offerings
    )
    output(
        title="Effects of the Ritual",
        text=f"Cards from the Hand: {from_hand}.",
    )

    altar.state = RitualState.COMPLETED
    return True


def judgement_effect(
    altar_index: int,
    game_state: GameState,
    test_only: bool = False,
) -> bool:
    altar = effect_verifier(
        rank=MajorArcanaRank.JUDGEMENT,
        altar_index=altar_index,
        game_state=game_state,
        allow_offerings=True,
    )

    if altar.state is not RitualState.COMPLETED:
        return False  # or None?

    compatible_discarded_cards: dict[MinorArcanaSuit, list[MinorArcana]] = {
        suit: []
        for suit in frozenset(offering.suit for offering in altar.offerings)
    }
    lookup_table: dict[str, MinorArcana] = {}
    for card in game_state.discard_pile:
        if card.suit in compatible_discarded_cards:
            compatible_discarded_cards[card.suit].append(card)
            lookup_table[str(card)] = card

    compatible_discarded_cards = {
        suit: cards
        for suit, cards in compatible_discarded_cards.items()
        if cards
    }
    if not compatible_discarded_cards:
        return False

    if test_only:
        return True

    all_possible_choices = [
        list(str(card) for card in comb)
        for suits in itertools.combinations(compatible_discarded_cards, 3)
        for comb in frozenset(
            itertools.product(
                *[compatible_discarded_cards[suit] for suit in suits]
            )
        )
    ]

    ask_choices = {
        "+".join(cards): " + ".join(cards) for cards in all_possible_choices
    }

    match len(all_possible_choices):
        case 0:
            return False
        case 1:
            selected_discarded_cards = next(iter(ask_choices))
        case _:
            selected_discarded_cards = ask(
                title="Select 3 cards from the discard pile",
                text=(
                    "The suit of the 3 cards you have to select must match"
                    " those of the offerings"
                ),
                choices=ask_choices,
                choices_min=1,
                choices_max=1,
            )

    selected_discarded_cards = selected_discarded_cards.split("+")
    for card_str in selected_discarded_cards:
        card = lookup_table[card_str]
        game_state.discard_pile.remove(card)
        game_state.offering_pile.append(card)
    random.shuffle(game_state.offering_pile)

    from_discard_pile = "[bright_black],[/bright_black] ".join(
        selected_discarded_cards
    )
    output(
        title="Effects of the Ritual",
        text=f"Cards from the Discard Pile: {from_discard_pile}.",
    )

    altar.state = RitualState.COMPLETED
    return True


def moon_effect(
    altar_index: int,
    game_state: GameState,
    test_only: bool = False,
) -> bool:
    altar = effect_verifier(
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
        return False

    if test_only:
        return True

    for hand_index in required_offerings_indexes:
        offering = game_state.hand[hand_index]
        game_state.hand[hand_index] = None
        altar.offerings.append(offering)  # pyright: ignore[reportArgumentType]

    from_hand = "[bright_black],[/bright_black] ".join(
        str(card) for card in altar.offerings
    )
    output(
        title="Effects of the Ritual",
        text=f"Cards from the Hand: {from_hand}.",
    )

    altar.state = RitualState.COMPLETED
    return True


def wheel_of_fortune_effect(
    altar_index: int,
    game_state: GameState,
    test_only: bool = False,
) -> bool:
    altar = effect_verifier(
        rank=MajorArcanaRank.WHEEL_OF_FORTUNE,
        altar_index=altar_index,
        game_state=game_state,
    )

    if len(game_state.discard_pile) < 3:
        return False

    choices = [
        index
        for index, offering in enumerate(game_state.hand)
        if isinstance(offering, MinorArcana)
    ]

    if len(choices) < 3:
        return False

    if test_only:
        return True

    random.shuffle(choices)
    hand_indexes_to_replace: list[int] = []
    for _ in range(3):
        hand_index = choices.pop()
        hand_indexes_to_replace.append(hand_index)
        offering = game_state.hand[hand_index]
        game_state.hand[hand_index] = None
        altar.offerings.append(offering)  # pyright: ignore[reportArgumentType]

    random.shuffle(game_state.discard_pile)
    for i in range(min(3, len(game_state.discard_pile))):
        offering = game_state.discard_pile.pop()
        hand_index = hand_indexes_to_replace[i]
        game_state.hand[hand_index] = offering

    from_hand = "[bright_black],[/bright_black] ".join(
        str(card) for card in altar.offerings[:3]
    )
    from_discard_pile = "[bright_black],[/bright_black] ".join(
        str(card) for card in altar.offerings[3:]
    )
    output(
        title="Effects of the Ritual",
        text=(
            f"Cards from the Hand: {from_hand}.\n"
            f"Cards from the Discard Pile: {from_discard_pile}."
        ),
    )

    altar.state = RitualState.COMPLETED
    return True


EFFECTS: dict[MajorArcanaRank, None | Effect] = {
    MajorArcanaRank.FOOL: fool_effect,
    MajorArcanaRank.MAGICIAN: None,
    MajorArcanaRank.HIGH_PRIESTESS: high_priestess_effect,
    MajorArcanaRank.EMPRESS: None,
    MajorArcanaRank.EMPEROR: None,
    MajorArcanaRank.HIEROPHANT: None,
    MajorArcanaRank.LOVERS: None,
    MajorArcanaRank.CHARIOT: None,
    MajorArcanaRank.JUSTICE: None,
    MajorArcanaRank.HERMIT: None,
    MajorArcanaRank.WHEEL_OF_FORTUNE: wheel_of_fortune_effect,
    MajorArcanaRank.STRENGTH: None,
    MajorArcanaRank.HANGED_MAN: None,
    MajorArcanaRank.DEATH: death_effect,
    MajorArcanaRank.TEMPERANCE: None,
    MajorArcanaRank.DEVIL: devil_effect,
    MajorArcanaRank.TOWER: None,
    MajorArcanaRank.STAR: None,
    MajorArcanaRank.MOON: moon_effect,
    MajorArcanaRank.SUN: None,
    MajorArcanaRank.JUDGEMENT: judgement_effect,
    MajorArcanaRank.WORLD: None,
}
