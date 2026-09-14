from __future__ import annotations

import typing

# from twentytwo_offerings.deck import (
from twentytwo_offerings.deck_with_orientation import (
    MajorArcanaRank,
    MinorArcana,
    MinorArcanaRank,
    MinorArcanaSuit,
)
from twentytwo_offerings.rituals import FIGURES, NUMBERED
from twentytwo_offerings.ui import ask

if typing.TYPE_CHECKING:
    from twentytwo_offerings.main import Altar, GameState


class Gift(typing.Protocol):
    def __call__(
        self,
        altar: Altar,
        game_state: GameState,
    ) -> MinorArcana | None: ...


def chariot_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
        if discarded_card.suit is MinorArcanaSuit.WANDS
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def death_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    return game_state.discard_pile.pop()


def devil_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(game_state.discard_pile[index]) for index in range(4)
    }

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def emperor_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
        if discarded_card.rank is MinorArcanaRank.QUEEN
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def empress_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
        if discarded_card.rank is MinorArcanaRank.KING
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def fool_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
    }

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def hanged_man_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
        if discarded_card.rank in (MinorArcanaRank.SIX, MinorArcanaRank.NINE)
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def hermit_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
        if discarded_card.rank is MinorArcanaRank.ACE
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def hierophant_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
        if discarded_card.rank is MinorArcanaRank.PAGE
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def high_priestess_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    return game_state.discard_pile.popleft()


def justice_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
        if discarded_card.rank is MinorArcanaRank.KNIGHT
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def lovers_gift(
    altar: Altar,
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    offering_suits = {offering.suit for offering in altar.offerings}

    choices = {
        str(index): str(card)
        for index, card in enumerate(game_state.discard_pile)
        if card.rank in FIGURES and card.suit not in offering_suits
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def magician_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
        if discarded_card.rank is MinorArcanaRank.THREE
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def moon_gift(
    altar: Altar,
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    offering_ranks = {offering.rank for offering in altar.offerings}

    choices = {
        str(index): str(card)
        for index, card in enumerate(game_state.discard_pile)
        if card.rank in offering_ranks
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def star_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(card)
        for index, card in enumerate(game_state.discard_pile)
        if card.suit is MinorArcanaSuit.CUPS
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def strength_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
        if discarded_card.suit is MinorArcanaSuit.SWORDS
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def sun_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(card)
        for index, card in enumerate(game_state.discard_pile)
        if card.suit is MinorArcanaSuit.COINS
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def temperance_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(card)
        for index, card in enumerate(game_state.discard_pile)
        if card.rank in NUMBERED and card.suit is MinorArcanaSuit.CUPS
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def tower_gift(
    altar: Altar,
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    offering_ranks = {offering.rank for offering in altar.offerings}

    choices = {
        str(index): str(card)
        for index, card in enumerate(game_state.discard_pile)
        if card.rank in offering_ranks
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


def world_gift(
    altar: Altar,  # pyright: ignore[reportUnusedParameter]
    game_state: GameState,
) -> MinorArcana | None:
    if not game_state.discard_pile:
        return None

    choices = {
        str(index): str(discarded_card)
        for index, discarded_card in enumerate(game_state.discard_pile)
        if discarded_card.rank is MinorArcanaRank.FOUR
    }

    if not choices:
        return None

    selected_index = ask(
        title="Select your Gift",
        text="Which card do you want?",
        choices=choices,
        choices_min=1,
        choices_max=1,
        result_caster=int,
    )
    card = game_state.discard_pile[selected_index]
    del game_state.discard_pile[selected_index]
    return card


GIFTS: dict[MajorArcanaRank, Gift | None] = {
    MajorArcanaRank.FOOL: fool_gift,
    MajorArcanaRank.MAGICIAN: magician_gift,
    MajorArcanaRank.HIGH_PRIESTESS: high_priestess_gift,
    MajorArcanaRank.EMPRESS: empress_gift,
    MajorArcanaRank.EMPEROR: emperor_gift,
    MajorArcanaRank.HIEROPHANT: hierophant_gift,
    MajorArcanaRank.LOVERS: lovers_gift,
    MajorArcanaRank.CHARIOT: chariot_gift,
    MajorArcanaRank.JUSTICE: justice_gift,
    MajorArcanaRank.HERMIT: hermit_gift,
    MajorArcanaRank.WHEEL_OF_FORTUNE: None,
    MajorArcanaRank.STRENGTH: strength_gift,
    MajorArcanaRank.HANGED_MAN: hanged_man_gift,
    MajorArcanaRank.DEATH: death_gift,
    MajorArcanaRank.TEMPERANCE: temperance_gift,
    MajorArcanaRank.DEVIL: devil_gift,
    MajorArcanaRank.TOWER: tower_gift,
    MajorArcanaRank.STAR: star_gift,
    MajorArcanaRank.MOON: moon_gift,
    MajorArcanaRank.SUN: sun_gift,
    MajorArcanaRank.JUDGEMENT: None,
    MajorArcanaRank.WORLD: world_gift,
}
