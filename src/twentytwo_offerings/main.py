from __future__ import annotations, unicode_literals

import argparse
import collections
import collections.abc
import dataclasses
import enum
import itertools
import random
import typing

from twentytwo_offerings.card_data import CARD_DATA, CardData
from twentytwo_offerings.deck import (
    MAJOR_ARCANA,
    MINOR_ARCANA,
    MajorArcana,
    MajorArcanaRank,
    MinorArcana,
    Orientation,
)
from twentytwo_offerings.gifts import GIFTS
from twentytwo_offerings.lib import (
    ALTARS_DATA,
    HAND_DATA,
    ContainerData,
    hand_row_indexes_by_offering_index,
)
from twentytwo_offerings.rituals import (
    BAD_RITUAL_STATES,
    RITUALS,
    OfferingType,
    RitualState,
)
from twentytwo_offerings.ui import Glyphs, ask, output

random.seed()


class Options(typing.TypedDict):
    gifts: bool


type MajorArcanaCards = collections.deque[MajorArcana]
type MinorArcanaCards = collections.deque[MinorArcana]


class ActionsLog(collections.UserList[dict[str, object]]):
    @typing.override
    def append(self, item: dict[str, object]) -> None:
        return self.data.append(item)


@dataclasses.dataclass
class Altar:
    arcana_card: MajorArcana
    offerings: list[MinorArcana]
    state: RitualState
    offering_type: OfferingType
    offering_src: MajorArcana

    @property
    def card_data(self) -> CardData:
        if self.offering_src.rank is self.arcana_card.rank:
            return CARD_DATA[self.arcana_card.rank]
        else:
            return CARD_DATA[self.offering_src.rank]

    def _(self, *, compact: bool = False) -> str:
        longest_name = max(
            len(major_arcana_rank.value)
            for major_arcana_rank in MajorArcanaRank
        )

        offerings = (
            "[bright_black],[/bright_black] ".join(
                str(offering) for offering in self.offerings
            )
            or f"[slate_blue1]{Glyphs.MID_X}[/slate_blue1]"
        )

        match self.offering_type:
            case OfferingType.AT_ONCE_AUTOMATIC:
                at_once = f"[bright_yellow]{Glyphs.V_ELLIPSIS}[/bright_yellow]"
            case OfferingType.AT_ONCE_MANUAL:
                at_once = f"[bright_yellow]{Glyphs.U_ELLIPSIS}[/bright_yellow]"
            case OfferingType.ONE_BY_ONE:
                at_once = f"[bright_cyan]{Glyphs.M_ELLIPSIS}[/bright_cyan]"
            case OfferingType.PROHIBITED:
                at_once = f"[bright_red]{Glyphs.PROHIBITED}[/bright_red]"

        match self.state:
            case RitualState.COMPLETED:
                state = f"[bright_green]{Glyphs.CHECK}[/bright_green]"
            case RitualState.EMPTY:
                if self.offering_type is OfferingType.PROHIBITED:
                    state = f"[bright_red]{Glyphs.LOCK_CLOSED}[/bright_red]"
                else:
                    # state = f"[purple]{Glyphs.EMPTY}[/purple]"
                    state = "[dodger_blue1]0[/dodger_blue1] "
            case RitualState.INVALID:
                state = f"[bright_red]{Glyphs.LOCK_CLOSED}[/bright_red]"
            case RitualState.LOCKED:
                state = f"[orange1]{Glyphs.GEAR}[/orange1]"
            case RitualState.PARTIAL:
                # state = f"[chartreuse4]{Glyphs.H_ELLIPSIS}[/chartreuse4]"
                state = f"[dodger_blue1]{len(self.offerings)}[/dodger_blue1] "
            case RitualState.READY:
                state = f"[pink1]{Glyphs.LOCK_OPEN}[/pink1]"

        if self.arcana_card is self.offering_src:
            src = ""
            description = self.card_data.ritual.description
        else:
            src = f" [{self.offering_src.rank}]"
            src_ritual = CARD_DATA[self.offering_src.rank].ritual
            description = f"[{src_ritual.description}]"

        card_name = self.arcana_card.rank  # .value
        orientation = self.arcana_card.orientation
        if compact:
            # card_name = self.arcana_card.rank.short
            return (
                f"[bold bright_white]"
                f"{card_name!s}{orientation!s}"
                f"[/bold bright_white]"
                f" {at_once} {state} [white]{offerings}[/white]"
            )
        else:
            padding = "⋅" * (longest_name - len(card_name))
            text = (
                f"{card_name!s}{orientation!s}"
                f"[bright_black]{padding}[/bright_black]"
            )
            return (
                f"{state} [bold bright_white]{text}[/bold bright_white]"
                f" [bright_black]-[/bright_black]"
                f" [chartreuse4]offerings: {offerings}[/chartreuse4]"
                f" {at_once}{src}"
                f" [bright_black italic]{description}[/bright_black italic]"
            )


type Altars = list[Altar | None]
type Hand = list[MinorArcana | None]
type Honored = collections.deque[Altar]


class Action(enum.StrEnum):
    DEBUG = "debug"
    SHOW_GAME_BOARD = "Show: the Game Board"
    SHOW_ACTIONS_LOG = "Show: the Actions Log"
    DEFEAT = "Defeat!"
    VICTORY = "Victory!"
    HONOR_COMPLETED_ALTARS = "Altar: Honor completed Altars"
    DRAW_OFFERINGS_TO_THE_HAND = "Draw Offerings to refill the Hand"
    MAKE_AN_OFFER = (
        f"Altar: Make an Offer with"
        f" [bright_cyan]{Glyphs.H_ELLIPSIS}[/bright_cyan]"
    )
    AUTO_HONOR = (
        f"Altar: Trigger an Altar with"
        f" [bright_yellow]{Glyphs.V_ELLIPSIS}[/bright_yellow]"
        f" or [bright_yellow]{Glyphs.U_ELLIPSIS}[/bright_yellow]"
    )
    DISCARD_TO_SEND_ONE_ARCANA_BACK = (
        "Discard: one card from the Hand to send one Arcana back"
    )
    DISCARD_TO_SEND_3_OFFERINGS_BACK_AND_DRAW_4_NEW_ONES = (
        "Discard: one card from the Hand to send 3 offerings back to the"
        " Offerings Pile and draw 4 new ones to refill the Hand"
    )

    @typing.override
    def __str__(self) -> str:
        return self.value


@dataclasses.dataclass
class GameState:
    arcana_pile: MajorArcanaCards
    altars: Altars
    honored_pile: Honored

    offering_pile: MinorArcanaCards
    hand: Hand
    discard_pile: MinorArcanaCards

    actions_log: ActionsLog

    # cards_orientation: dict[MajorArcana | MinorArcana, Orientation]
    options: Options

    @property
    def score(self) -> int:
        return len(self.honored_pile)

    @property
    def state(self) -> typing.Literal[Action.DEFEAT, Action.VICTORY, None]:

        if all(altar is None for altar in self.altars):
            if self.arcana_pile:
                raise RuntimeError(
                    (
                        "If Altars are empty,"
                        " major arcana cards must refill the altars!"
                    )
                )
            else:
                return Action.VICTORY

        if all(offering is None for offering in self.hand):
            if self.offering_pile:
                raise RuntimeError(
                    "If Hand is empty, offerings must refill the Hand!"
                )
            else:
                return Action.DEFEAT

        if self.arcana_pile:
            return None

        for altar_index, altar in enumerate(self.altars):
            if altar is None:
                continue

            if altar.state in BAD_RITUAL_STATES:
                raise RuntimeError(
                    "Altars must be either None or in a valid State!"
                )

            for offering_index, offering in enumerate(self.hand):
                if offering is None:
                    continue

                possible_new_state = self.test_offering(
                    altar_index=altar_index,
                    offering_index=offering_index,
                )
                if possible_new_state not in BAD_RITUAL_STATES:
                    return None

        return Action.DEFEAT

    def test_offering(
        self,
        altar_index: int,
        offering_index: int,
    ) -> typing.Literal[OfferingType.PROHIBITED] | RitualState:

        altar = self.altars[altar_index]
        if altar is None or altar.state in (
            RitualState.INVALID,
            RitualState.COMPLETED,
        ):
            return OfferingType.PROHIBITED

        offering = self.hand[offering_index]
        if offering is None:
            return OfferingType.PROHIBITED

        self.hand[offering_index] = altar.offerings.append(offering)

        possible_new_state = altar.card_data.ritual.get_state(
            altar_index=altar_index,
            game_state=self,
        )

        if possible_new_state is RitualState.INVALID:
            self.hand[offering_index] = altar.offerings.pop()

        return possible_new_state

    def _make_and_add_new_altar(
        self,
        altar_index: int,
        arcana_card: MajorArcana,
    ) -> Altar:
        altar = Altar(
            arcana_card=arcana_card,
            state=RitualState.EMPTY,
            offerings=[],
            offering_type=OfferingType.PROHIBITED,
            offering_src=arcana_card,
        )
        self.altars[altar_index] = altar

        ritual = CARD_DATA[arcana_card.rank].ritual
        altar.offering_type, altar.offering_src = ritual.get_offering_type(
            altar_index=altar_index,
            game_state=self,
        )
        altar.state = ritual.get_state(
            altar_index=altar_index,
            game_state=self,
        )

        output(
            title="New Altar",
            text=(
                f"[italic]A new altar for the[/italic]"
                f" [bright_white bold]{altar.arcana_card}[/bright_white bold]"
                f" [italic]has just been erected<i={altar_index + 1}>![/italic]"
            ),
        )

        return altar

    def replenish_altars(
        self,
        altar_indexes: collections.abc.Sequence[int] = (),
    ) -> int:
        created = 0

        if not altar_indexes:
            altar_indexes = range(ALTARS_DATA.slots)

        for altar_index in altar_indexes:
            if isinstance(self.altars[altar_index], Altar):
                continue

            try:
                arcana_card = self.arcana_pile.popleft()
            except IndexError:
                break

            altar = self._make_and_add_new_altar(
                altar_index=altar_index,
                arcana_card=arcana_card,
            )
            created += 1

            self.actions_log.append(
                {
                    "action": "replenish_altars",
                    "altar_index": altar_index,
                    "arcana_card": altar.arcana_card,
                }
            )

            # Is this card the Major Arcana Devil card? (keep tests generic)
            if (
                altar.offering_type is OfferingType.AT_ONCE_AUTOMATIC
                and callable(altar.card_data.effect)
                and altar.card_data.effect(
                    altar_index=altar_index,
                    game_state=self,
                )
            ):
                self.honor_completed_altars(altar_indexes=[altar_index])
                _ = self.replenish_hand()

        return created

    def _has_honoring_completed_a_ritual(self) -> None:
        for altar_index, altar in enumerate(self.altars):
            if altar is None:
                # probably the devil during init_game_state()
                continue

            # necessary for the Fool
            ritual = RITUALS[altar.arcana_card.rank]
            altar.state = ritual.get_state(
                altar_index=altar_index,
                game_state=self,
            )
            altar.offering_type = ritual.get_offering_type(
                altar_index=altar_index,
                game_state=self,
            )[0]

    def _has_discarding_completed_a_ritual(self) -> None:
        for altar_index, altar in enumerate(self.altars):
            if altar is None:
                # probably the devil during init_game_state()
                continue

            # necessary for the Fool and the Judgement
            ritual = RITUALS[altar.arcana_card.rank]
            altar.state = ritual.get_state(
                altar_index=altar_index,
                game_state=self,
            )
            if altar.state is RitualState.COMPLETED:
                self._honor_completed_altar(altar_index=altar_index)

    def discard_to_send_one_arcana_back(
        self,
        altar_index: int,
        offering_index: int,
    ) -> None:
        altar = self.altars[altar_index]
        if altar is None:
            raise ValueError(f"Altars[{altar_index}] is None!")

        if not altar.card_data.can_be_sent_back:
            raise RuntimeError(
                (
                    f"You can't sent the {altar.arcana_card} card"
                    f" back to the Arcana Pile"
                )
            )

        offering = self.hand[offering_index]
        if offering is None:
            raise ValueError(f"Hand[{offering_index}] is None!")

        self.actions_log.append(
            {
                "action": "discard_to_send_back_one_arcana",
                "altar_index": altar_index,
                "arcana_card": altar.arcana_card,
                "offering_index": offering_index,
                "offering": offering,
            }
        )
        output(
            title="Discarded Offering",
            text=f"{offering!s} [italic]has just been discarded![/italic]",
        )

        self.hand[offering_index] = None
        self.discard_pile.appendleft(offering)

        output(
            title="Arcana sent back",
            text=(
                f"[bright_white bold]{altar.arcana_card!s}[/bright_white bold]"
                f" [italic]has just been sent back to the Arcana Pile![/italic]"
            ),
        )

        _ = self.replenish_hand(offering_indexes=[offering_index])

        self.altars[altar_index] = None
        self.arcana_pile.append(altar.arcana_card)
        self.discard_pile.extendleft(altar.offerings)
        _ = self.replenish_altars(altar_indexes=[altar_index])

        self._has_discarding_completed_a_ritual()

    def discard_to_send_3_offerings_back_and_draw_4_new_ones(
        self,
        offering_index: int,
    ) -> None:
        offering = self.hand[offering_index]
        if offering is None:
            raise ValueError(f"Hand[{offering_index}] is None!")

        self.hand[offering_index] = None
        self.discard_pile.appendleft(offering)

        affected_indexes = tuple(
            hand_row_indexes_by_offering_index(offering_index=offering_index)
        )
        for index in affected_indexes:
            item = self.hand[index]

            if index != offering_index and isinstance(item, MinorArcana):
                self.offering_pile.append(item)
                self.hand[index] = None

        self.actions_log.append(
            {
                "action": (
                    "discard_to_send_3_offerings_back_and_draw_4_new_ones"
                ),
                "offering_index": offering_index,
                "offering": offering,
            }
        )
        output(
            title="Discarded Offering",
            text=f"{offering!s} [italic]has just been discarded![/italic]",
        )

        _ = self.replenish_hand(offering_indexes=affected_indexes)

        self._has_discarding_completed_a_ritual()

    def discard_altar(self, altar_index: int) -> None:
        altar = self.altars[altar_index]
        if altar is None:
            raise ValueError(f"Altars[{altar_index}] is None!")

        if altar.state is not RitualState.COMPLETED:
            raise RuntimeError("Altar state was expected to be COMPLETED!")

        self.honored_pile.appendleft(altar)
        self.altars[altar_index] = None

        self.actions_log.append(
            {
                "action": "discard_altar",
                "altar_index": altar_index,
                "arcana_card": altar.arcana_card,
            }
        )

    def honor_completed_altars(
        self,
        altar_indexes: collections.abc.Sequence[int] = (),
    ) -> None:
        if not altar_indexes:
            altar_indexes = range(ALTARS_DATA.slots)

        for altar_index in altar_indexes:
            altar = self.altars[altar_index]
            if altar is None:
                continue

            altar.state = altar.card_data.ritual.get_state(
                altar_index=altar_index,
                game_state=self,
            )
            if altar.state is RitualState.COMPLETED:
                self._honor_completed_altar(altar_index=altar_index)

    def _handle_altar_orientation(self, altar: Altar):
        altar_orientation = altar.arcana_card.orientation

        offering_matching_orientation_with_arcana_card = sum(
            1
            for offering in altar.offerings
            if offering.orientation is altar_orientation
        )
        if offering_matching_orientation_with_arcana_card == 0:
            self.discard_pile.appendleft(self.offering_pile.popleft())
        elif float(offering_matching_orientation_with_arcana_card) < 0.5 * (
            len(altar.offerings)
        ):
            return

        gift = GIFTS[altar.arcana_card.rank]
        if not self.options["gifts"] or not callable(gift):
            return

        card = gift(altar=altar, game_state=self)
        if not isinstance(card, MinorArcana):
            return

        output(
            title="Gift from the Altar",
            text=(
                f"[bright_white bold]{altar.arcana_card!s}[/bright_white bold]"
                f" [italic]has gifted you a[/italic]"
                f" {card!s}[italic]![/italic]"
            ),
        )

        nones_in_hand = tuple(
            index for index, card in enumerate(self.hand) if card is None
        )
        match len(nones_in_hand):
            case 0:
                raise RuntimeError(
                    "There should be at least one None in the Hand!"
                )
            case 1:
                target_index = nones_in_hand[0]
            case _:
                choices: dict[str, str] = {}
                for index in nones_in_hand:
                    row, column = divmod(index, HAND_DATA.slots // 2)
                    choices[str(index)] = f"r={row + 1} c={column + 1}"
                target_index = ask(
                    title="Position the gift",
                    text=(
                        "Where do you want to place the gift"
                        " you've received?"
                    ),
                    choices=choices,
                    choices_min=1,
                    choices_max=1,
                    result_caster=int,
                )
        self.hand[target_index] = card

    def _honor_completed_altar(self, altar_index: int) -> None:
        altar = self.altars[altar_index]
        if altar is None:
            raise ValueError(f"Altars[{altar_index}] is None!")

        self.actions_log.append(
            {
                "action": "honor_completed_altar",
                "altar_index": altar_index,
                "arcana_card": altar.arcana_card,
            }
        )

        output(
            title="Ritual Completed",
            text=(
                f"[bright_white bold]{altar.arcana_card}[/bright_white bold]"
                f" [italic]moves to the Honored Pile![/italic]"
            ),
        )

        self._handle_altar_orientation(altar=altar)
        self.discard_altar(altar_index=altar_index)
        _ = self.replenish_altars(altar_indexes=[altar_index])

        for altar_index, altar in enumerate(self.altars):
            if altar is None:
                # probably the devil during init_game_state()
                continue

            # necessary for the Fool
            ritual = RITUALS[altar.arcana_card.rank]
            altar.state = ritual.get_state(
                altar_index=altar_index,
                game_state=self,
            )
            altar.offering_type = ritual.get_offering_type(
                altar_index=altar_index,
                game_state=self,
            )[0]

    def replenish_hand(
        self,
        offering_indexes: collections.abc.Sequence[int] = (),
    ) -> int:
        created = 0

        if not offering_indexes:
            offering_indexes = range(HAND_DATA.slots)

        for offering_index in offering_indexes:
            if isinstance(self.hand[offering_index], MinorArcana):
                continue

            try:
                offering = self.offering_pile.popleft()
            except IndexError:
                break

            self.hand[offering_index] = offering
            created += 1

            self.actions_log.append(
                {
                    "action": "replenish_hand",
                    "offering_index": offering_index,
                    "offering": offering,
                }
            )

            row, column = divmod(offering_index, HAND_DATA.slots // 2)
            output(
                title="New Offering Available",
                text=(
                    f"{offering!s}"
                    f" [italic]has just been added to your Hand"
                    f"<r={row + 1}, c={column + 1}>![/italic]"
                ),
            )

        return created

    def auto_honor(self, altar_index: int) -> None:
        altar = self.altars[altar_index]
        if altar is None:
            raise ValueError(f"Altars[{altar_index}] is None!")

        ritual_state = altar.state
        if ritual_state not in (
            RitualState.EMPTY,
            RitualState.LOCKED,
            RitualState.PARTIAL,
            RitualState.READY,
        ):
            raise ValueError(
                f"{altar.arcana_card!s}'s {ritual_state=} blocks interactions"
            )

        match altar.offering_type:
            case OfferingType.AT_ONCE_AUTOMATIC if callable(
                altar.card_data.effect
            ):
                output(
                    title="Evocation",
                    text=(
                        f"[italic]You are trying to evoke the[/italic]"
                        f" [bright_white bold]{altar.arcana_card!s}"
                        f"[/bright_white bold][italic]...[/italic]"
                    ),
                )
                if not altar.card_data.effect(
                    altar_index=altar_index,
                    game_state=self,
                ):
                    output(
                        title=f"{Glyphs.WARNING} Error",
                        text=(
                            f"[bright_white bold]"
                            f"{altar.arcana_card!s}"
                            f"[/bright_white bold]"
                            f" [red]has just refused the ritual![/red]"
                        ),
                    )
            case OfferingType.AT_ONCE_MANUAL if callable(
                altar.card_data.effect
            ):
                output(
                    title="Evocation",
                    text=(
                        f"[italic]You are trying to evoke the[/italic]"
                        f" [bright_white bold]{altar.arcana_card!s}"
                        f"[/bright_white bold][italic]...[/italic]"
                    ),
                )
                if not altar.card_data.effect(
                    altar_index=altar_index,
                    game_state=self,
                ):
                    output(
                        title=f"{Glyphs.WARNING} Error",
                        text=(
                            f"[bright_white bold]"
                            f"{altar.arcana_card!s}"
                            f"[/bright_white bold]"
                            f" [red]has just refused the ritual![/red]"
                        ),
                    )
            case OfferingType.PROHIBITED:
                output(
                    title=f"{Glyphs.WARNING} Error",
                    text=(
                        f"[red] You can't make an offer to[/red]"
                        f" [bright_white bold]"
                        f"{altar.arcana_card!s}"
                        f"[/bright_white bold][italic]![/italic]"
                    ),
                )
            case _:
                return

        self.actions_log.append(
            {
                "action": "auto_honor",
                "altar_index": altar_index,
                "arcana_card": altar.arcana_card,
            }
        )

        _ = self.replenish_hand()
        self.honor_completed_altars(altar_indexes=[altar_index])

    def _one_by_one_offer(
        self,
        altar_index: int,
        altar: Altar,
        offering_index: int,
        offering: MinorArcana,
    ) -> None:
        current_state = dataclasses.replace(self, **{})
        outcome = self.test_offering(
            altar_index=altar_index,
            offering_index=offering_index,
        )
        if outcome in (
            RitualState.INVALID,
            OfferingType.PROHIBITED,
        ):
            output(
                title=f"{Glyphs.WARNING} Error",
                text=(
                    f"[white bold]{altar.arcana_card!s}[/white bold]"
                    f" [red]has refused[/red] {offering!s}[red]![/red]"
                ),
            )
            for field in dataclasses.fields(current_state):
                field_name = field.name
                setattr(self, field_name, getattr(current_state, field_name))
            return

        if callable(altar.card_data.effect) and not altar.card_data.effect(
            altar_index=altar_index,
            game_state=self,
        ):
            for field in dataclasses.fields(current_state):
                field_name = field.name
                setattr(self, field_name, getattr(current_state, field_name))
            return

        altar.state = outcome
        output(
            title="Offering Accepted",
            text=(
                f"[bright_white bold]{altar.arcana_card!s}[/bright_white bold]"
                f" [italic]has accepted your offering of a[/italic]"
                f" {offering!s}"
            ),
        )

    def make_an_offer(self, altar_index: int, offering_index: int) -> None:
        altar = self.altars[altar_index]
        if altar is None:
            raise ValueError(f"Altars[{altar_index}] is None!")

        ritual_state = altar.state
        if ritual_state not in (
            RitualState.EMPTY,
            RitualState.LOCKED,
            RitualState.PARTIAL,
            # RitualState.READY,
        ):
            raise ValueError(
                f"{altar.arcana_card!s}'s {ritual_state=} blocks interactions"
            )

        offering = self.hand[offering_index]
        if offering is None:
            raise ValueError(f"Hand[{offering_index}] is None!")

        match altar.offering_type:
            case OfferingType.ONE_BY_ONE:
                self._one_by_one_offer(
                    altar_index=altar_index,
                    altar=altar,
                    offering_index=offering_index,
                    offering=offering,
                )
            case OfferingType.PROHIBITED:
                output(
                    title=f"{Glyphs.WARNING} Error",
                    text=f"You can't make an offer to {altar.arcana_card!s}!",
                )
            case _:
                return

        self.actions_log.append(
            {
                "action": "make_an_offer",
                "altar_index": altar_index,
                "arcana_card": altar.arcana_card,
                "offering_index": offering_index,
                "offering": offering,
            }
        )

        _ = self.replenish_hand(offering_indexes=[offering_index])
        self.honor_completed_altars(altar_indexes=[altar_index])

    def calculate_actions(self) -> list[Action]:
        if len(self.actions_log) == 1:
            completed_altar_indexes = [
                altar_index
                for altar_index, altar in enumerate(self.altars)
                if altar is not None
                and altar.card_data.ritual.get_state(
                    altar_index=altar_index,
                    game_state=self,
                )
                is RitualState.COMPLETED
            ]
            if completed_altar_indexes:
                return [Action.HONOR_COMPLETED_ALTARS]

        state = self.state
        if state is not None:
            return [state]

        if self.offering_pile and HAND_DATA.slots > sum(
            1 for offering in self.hand if offering is not None
        ):
            return [Action.DEBUG, Action.DRAW_OFFERINGS_TO_THE_HAND]

        actions: list[Action] = []

        if any(
            altar
            for altar_index, altar in enumerate(self.altars)
            if altar is not None
            and altar.offering_type is OfferingType.ONE_BY_ONE
            and altar.card_data.ritual.get_state(
                altar_index=altar_index,
                game_state=self,
            )
            is not RitualState.INVALID
        ):
            actions.append(Action.MAKE_AN_OFFER)

        if any(
            altar
            for altar_index, altar in enumerate(self.altars)
            if altar is not None
            and altar.offering_type
            in (
                OfferingType.AT_ONCE_AUTOMATIC,
                OfferingType.AT_ONCE_MANUAL,
            )
            and altar.card_data.ritual.get_state(
                altar_index=altar_index,
                game_state=self,
            )
            is not RitualState.INVALID
        ):
            actions.append(Action.AUTO_HONOR)

        actions.extend(
            (
                Action.DEBUG,
                Action.SHOW_ACTIONS_LOG,
                Action.SHOW_GAME_BOARD,
            )
        )
        if self.arcana_pile:
            actions.append(Action.DISCARD_TO_SEND_ONE_ARCANA_BACK)
        if self.offering_pile:
            actions.append(
                Action.DISCARD_TO_SEND_3_OFFERINGS_BACK_AND_DRAW_4_NEW_ONES
            )

        return actions

    def show_actions_log(self) -> None:
        output(
            title="Actions",
            text="\n".join(
                "[bright_black],[/bright_black] ".join(
                    f"{k!s}: {v!s}" for k, v in action.items()
                )
                for action in self.actions_log
            ),
        )

    def show_game_board(self) -> None:
        params: dict[str, str] = {
            "len_ap": str(len(self.arcana_pile)),
            "len_dp": str(len(self.discard_pile)),
            "len_hp": str(len(self.honored_pile)),
            "len_op": str(len(self.offering_pile)),
        }
        params.update(
            (
                key[-2:],
                f"{key[-2].upper()}:#[dodger_blue1]{value:>02}[/dodger_blue1]",
            )
            for key, value in params.copy().items()
        )
        max_length = max(len(rank.value) for rank in MajorArcanaRank)
        if max_length % 2:
            width = max_length + 1
        else:
            width = max_length
        params.update(
            (
                f"_{index}",
                (
                    (
                        # f"[bright_white bold]{altar.arcana_card.rank.short}"
                        f"[bright_white bold]"
                        f"{altar.arcana_card._(compact=True, width=width)}"
                        f"[/bright_white bold]:"
                        f"[dodger_blue1]{len(altar.offerings)}[/dodger_blue1]"
                    )
                    if altar is not None
                    else "-"
                ),
            )
            for index, altar in enumerate(self.altars)
        )
        params.update(
            (
                f"a{altar_index}",
                "-" if altar is None else altar._(),
            )
            for altar_index, altar in enumerate(self.altars)
        )
        # -2 is 3 - 5
        # 3 is len(": x") where x is the number of offerings of the altar
        # 5 is len(str(MinorArcana))
        padding = max_length - 2
        if padding % 2:
            # this must be even to allow 2 × "// 2" on the same line
            padding += 1
        padding = " " * (padding // 2)
        params.update(
            (f"h{index}", f"{padding}{offering!s}{padding}")
            for index, offering in enumerate(self.hand)
        )
        params["sp"] = " " * 4

        honored = " [dark_green]|||[/dark_green] ".join(
            altar._(compact=True) for altar in self.honored_pile
        )
        discarded = "[bright_black],[/bright_black] ".join(
            str(card) for card in self.discard_pile
        )

        empty = f"[purple]{Glyphs.EMPTY}[/purple]"
        text = (
            "{ap}".format(**params),
            "{sp}›{a0}‹".format(**params),
            "{sp}›{a1}‹".format(**params),
            "{sp}›{a2}‹".format(**params),
            "{sp}›{a3}‹".format(**params),
            "{hp} - {hl}".format(hl=honored or empty, **params),
            "",
            "{sp}›{_0}‹   ›{_1}‹   ›{_2}‹   ›{_3}‹".format(**params),
            "{op}".format(**params),
            "{sp}›{h0}‹   ›{h1}‹   ›{h2}‹   ›{h3}‹".format(**params),
            "{sp}›{h4}‹   ›{h5}‹   ›{h6}‹   ›{h7}‹".format(**params),
            "{dp} - {dl}".format(dl=discarded or empty, **params),
            "",
        )
        output(title="game board", text="\n".join(text))


class TwentyTwoOfferings:
    def __init__(self) -> None:
        self._game_state: GameState
        self.init_game_state()

    @property
    def game_state(self) -> GameState:
        return self._game_state

    def _set_cards_orientation(self, options: Options) -> None:
        if options["gifts"]:
            for cards in (MAJOR_ARCANA, MINOR_ARCANA):
                cards_in_half_a_deck = len(cards) // 2
                orientations: list[Orientation] = list(
                    itertools.chain(
                        [Orientation.NORMAL] * cards_in_half_a_deck,
                        [Orientation.INVERTED] * cards_in_half_a_deck,
                    )
                )
                random.shuffle(orientations)
                for card, orientation in zip(cards, orientations):
                    card.orientation = orientation
        else:
            for card in itertools.chain(MAJOR_ARCANA, MINOR_ARCANA):
                card.orientation = Orientation.NORMAL

    def init_game_state(self) -> None:
        options = get_command_line_options()
        # cards_orientation = self._get_cards_orientation(options=options)
        self._set_cards_orientation(options=options)

        arcana_pile: MajorArcanaCards = collections.deque()
        arcana_pile.extend(MAJOR_ARCANA)
        random.shuffle(arcana_pile)
        altars: Altars = [None] * ALTARS_DATA.slots
        honored_pile: Honored = collections.deque()

        offering_pile: MinorArcanaCards = collections.deque()
        offering_pile.extend(MINOR_ARCANA)
        random.shuffle(offering_pile)
        hand: Hand = [None] * HAND_DATA.slots
        discard_pile: MinorArcanaCards = collections.deque()

        self._game_state = GameState(
            arcana_pile=arcana_pile,
            altars=altars,
            honored_pile=honored_pile,
            offering_pile=offering_pile,
            hand=hand,
            discard_pile=discard_pile,
            actions_log=ActionsLog(),
            # cards_orientation=cards_orientation,
            options=options,
        )

        if self._game_state.replenish_hand() != HAND_DATA.slots:
            raise RuntimeError("Couldn't init hand!")

        if self._game_state.replenish_altars() != ALTARS_DATA.slots:
            raise RuntimeError("Couldn't init altars!")

        self._game_state.actions_log.append({"action": "init_game_state"})

    def _stringify(self, item: Altar | MinorArcana) -> str:
        if isinstance(item, MinorArcana):
            return str(item)

        return item._()

    def ask_contaner_slot_index(
        self,
        container_data: ContainerData,
        indexes: collections.abc.Sequence[int] = (),
    ) -> int:
        if not indexes:
            indexes = tuple(range(container_data.slots))

        if container_data.name == "altars":
            game_state_attribute = typing.cast(
                Altars,
                getattr(
                    self._game_state,
                    container_data.game_state_attribute_name,
                ),
            )
        else:
            game_state_attribute = typing.cast(
                Hand,
                getattr(
                    self._game_state,
                    container_data.game_state_attribute_name,
                ),
            )

        return ask(
            title=f"Select from the {container_data.name}",
            text=f"{container_data.content}»index: ",
            choices={
                str(index): self._stringify(item)
                for index, item in enumerate(game_state_attribute)
                if item is not None and index in indexes
            },
            choices_min=1,
            choices_max=1,
            result_caster=int,
        )

    def run(self) -> None:
        while True:
            self._game_state.show_game_board()

            available_actions = self._game_state.calculate_actions()

            if len(available_actions) == 1:
                selected_action = available_actions[0]
            else:
                choices = {
                    action.value: f"[grey74]{action.value}[/grey74]"
                    for action in available_actions
                }
                selected_action: Action = ask(
                    title="Select 1 action",
                    text="Select your next action",
                    choices=choices,
                    choices_min=1,
                    choices_max=1,
                    result_caster=Action,
                )

            match selected_action:
                case Action.SHOW_GAME_BOARD:
                    self._game_state.show_game_board()

                case Action.SHOW_ACTIONS_LOG:
                    self._game_state.show_actions_log()

                case Action.DEBUG:
                    import pdb

                    pdb.set_trace()

                case Action.DEFEAT | Action.VICTORY:
                    output(
                        title="Game Over",
                        text=(
                            f"[underline overline bold]"
                            f"{selected_action.value}"
                            f"[/underline overline bold]"
                        ),
                    )
                    break

                case Action.HONOR_COMPLETED_ALTARS:
                    _ = self._game_state.honor_completed_altars()

                case Action.DRAW_OFFERINGS_TO_THE_HAND:
                    _ = self._game_state.replenish_hand()

                case Action.AUTO_HONOR:
                    altar_index = self.ask_contaner_slot_index(
                        container_data=ALTARS_DATA,
                        indexes=tuple(
                            altar_index
                            for altar_index, altar in enumerate(
                                self._game_state.altars
                            )
                            if altar is not None
                            and altar.offering_type
                            in (
                                OfferingType.AT_ONCE_AUTOMATIC,
                                OfferingType.AT_ONCE_MANUAL,
                            )
                        ),
                    )
                    self._game_state.auto_honor(altar_index=altar_index)

                case Action.MAKE_AN_OFFER:
                    altar_index = self.ask_contaner_slot_index(
                        container_data=ALTARS_DATA,
                        indexes=tuple(
                            altar_index
                            for altar_index, altar in enumerate(
                                self._game_state.altars
                            )
                            if altar is not None
                            and altar.offering_type is OfferingType.ONE_BY_ONE
                        ),
                    )
                    offering_index = self.ask_contaner_slot_index(
                        container_data=HAND_DATA, indexes=tuple()
                    )
                    self._game_state.make_an_offer(
                        altar_index=altar_index,
                        offering_index=offering_index,
                    )

                case Action.DISCARD_TO_SEND_ONE_ARCANA_BACK:
                    altar_index = self.ask_contaner_slot_index(ALTARS_DATA)
                    offering_index = self.ask_contaner_slot_index(HAND_DATA)
                    self._game_state.discard_to_send_one_arcana_back(
                        altar_index=altar_index,
                        offering_index=offering_index,
                    )

                case (
                    Action.DISCARD_TO_SEND_3_OFFERINGS_BACK_AND_DRAW_4_NEW_ONES
                ):
                    offering_index = self.ask_contaner_slot_index(HAND_DATA)
                    self._game_state.discard_to_send_3_offerings_back_and_draw_4_new_ones(
                        offering_index=offering_index,
                    )


def get_command_line_options() -> Options:
    parser = argparse.ArgumentParser(
        description="Terminal implementation of the '22 Offerings' tarot game",
        epilog=(
            "Read the game rules at"
            " https://boardgamegeek.com/boardgame/321659/22-offerings"
        ),
    )
    _ = parser.add_argument("-g", "--gifts", action="store_true")
    parsed = parser.parse_args()
    return Options(gifts=typing.cast(bool, parsed.gifts))


if __name__ == "__main__":
    tto = TwentyTwoOfferings()
    tto.run()
