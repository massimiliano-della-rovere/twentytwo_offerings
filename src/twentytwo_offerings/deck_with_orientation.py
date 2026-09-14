from __future__ import unicode_literals

import abc
import collections.abc
import dataclasses
import enum
import itertools
import typing

from twentytwo_offerings.ui import Glyphs


class Orientation(enum.StrEnum):
    NORMAL = enum.auto()
    INVERTED = enum.auto()

    @typing.override
    def __str__(self) -> str:
        return {
            Orientation.NORMAL: Glyphs.ARROW_UP,
            Orientation.INVERTED: Glyphs.ARROW_DOWN,
        }[self]


class Card[R, S](abc.ABC):
    orientation: Orientation
    _rank: R = dataclasses.field(  # pyright: ignore[reportAny]
        init=True,
        repr=False,
    )
    _suit: S = dataclasses.field(  # pyright: ignore[reportAny]
        init=True,
        repr=False,
    )

    @typing.override
    @abc.abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError

    @property
    def rank(self) -> R:
        return self._rank

    @property
    def suit(self) -> S:
        return self._suit


class MajorArcanaRank(enum.StrEnum):
    FOOL = "Fool"
    MAGICIAN = "Magician"
    HIGH_PRIESTESS = "High Priestess"
    EMPRESS = "Empress"
    EMPEROR = "Emperor"
    HIEROPHANT = "Hierophant"
    LOVERS = "Lovers"
    CHARIOT = "Chariot"
    JUSTICE = "Justice"
    HERMIT = "Hermit"
    WHEEL_OF_FORTUNE = "Wheel of Fortune"
    STRENGTH = "Strength"
    HANGED_MAN = "Hanged Man"
    DEATH = "Death"
    TEMPERANCE = "Temperance"
    DEVIL = "Devil"
    TOWER = "Tower"
    STAR = "Star"
    MOON = "Moon"
    SUN = "Sun"
    JUDGEMENT = "Judgement"
    WORLD = "World"

    def __int__(self) -> int:
        match self:
            case MajorArcanaRank.FOOL:
                return 0
            case MajorArcanaRank.MAGICIAN:
                return 1
            case MajorArcanaRank.HIGH_PRIESTESS:
                return 2
            case MajorArcanaRank.EMPRESS:
                return 3
            case MajorArcanaRank.EMPEROR:
                return 4
            case MajorArcanaRank.HIEROPHANT:
                return 5
            case MajorArcanaRank.LOVERS:
                return 6
            case MajorArcanaRank.CHARIOT:
                return 7
            case MajorArcanaRank.JUSTICE:
                return 8
            case MajorArcanaRank.HERMIT:
                return 9
            case MajorArcanaRank.WHEEL_OF_FORTUNE:
                return 10
            case MajorArcanaRank.STRENGTH:
                return 11
            case MajorArcanaRank.HANGED_MAN:
                return 12
            case MajorArcanaRank.DEATH:
                return 13
            case MajorArcanaRank.TEMPERANCE:
                return 14
            case MajorArcanaRank.DEVIL:
                return 15
            case MajorArcanaRank.TOWER:
                return 16
            case MajorArcanaRank.STAR:
                return 17
            case MajorArcanaRank.MOON:
                return 18
            case MajorArcanaRank.SUN:
                return 19
            case MajorArcanaRank.JUDGEMENT:
                return 20
            case MajorArcanaRank.WORLD:
                return 21

    @property
    def short(self) -> str:
        match self:
            case MajorArcanaRank.FOOL:
                return " fool"
            case MajorArcanaRank.MAGICIAN:
                return "magic"
            case MajorArcanaRank.HIGH_PRIESTESS:
                return "hprie"
            case MajorArcanaRank.EMPRESS:
                return "emprs"
            case MajorArcanaRank.EMPEROR:
                return "emper"
            case MajorArcanaRank.HIEROPHANT:
                return "hiero"
            case MajorArcanaRank.LOVERS:
                return "lover"
            case MajorArcanaRank.CHARIOT:
                return "chari"
            case MajorArcanaRank.JUSTICE:
                return "justi"
            case MajorArcanaRank.HERMIT:
                return "hermi"
            case MajorArcanaRank.WHEEL_OF_FORTUNE:
                return "whoff"
            case MajorArcanaRank.STRENGTH:
                return "stren"
            case MajorArcanaRank.HANGED_MAN:
                return "h_man"
            case MajorArcanaRank.DEATH:
                return "death"
            case MajorArcanaRank.TEMPERANCE:
                return "tempe"
            case MajorArcanaRank.DEVIL:
                return "devil"
            case MajorArcanaRank.TOWER:
                return "tower"
            case MajorArcanaRank.STAR:
                return " star"
            case MajorArcanaRank.MOON:
                return " moon"
            case MajorArcanaRank.SUN:
                return " sun "
            case MajorArcanaRank.JUDGEMENT:
                return "judge"
            case MajorArcanaRank.WORLD:
                return "world"


class MajorArcanaSuit(enum.StrEnum):
    MAJOR_ARCANA = enum.auto()


@dataclasses.dataclass  # (frozen=True)
class MajorArcana(Card[MajorArcanaRank, MajorArcanaSuit]):
    orientation: Orientation
    _rank: MajorArcanaRank = dataclasses.field(init=True, repr=False)
    _suit: MajorArcanaSuit = dataclasses.field(init=True, repr=False)

    @typing.override
    def __str__(self) -> str:
        return self._(compact=False)

    def _(self, compact: bool = False, width: int = 0) -> str:
        if compact:
            rank = ""
        else:
            rank = f"[white]{int(self.rank)}[/white] "
            if int(self.rank) < 10:
                rank = f"[bright_black]⋅[/bright_black]{rank}"

        text = f"{rank}[white]{self.rank.value}{self.orientation!s}[/white]"

        if width == 0:
            return text

        width -= len(self.rank.value)
        padding_r = width // 2
        padding_l = width - padding_r
        return f"{" " * padding_l}{text}{" " * padding_r}"


class MinorArcanaRank(enum.StrEnum):
    ACE = "A"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    PAGE = "P"
    KNIGHT = "J"
    QUEEN = "Q"
    KING = "K"

    def __int__(self) -> int:
        match self:
            case MinorArcanaRank.ACE:
                return 1
            case MinorArcanaRank.TWO:
                return 2
            case MinorArcanaRank.THREE:
                return 3
            case MinorArcanaRank.FOUR:
                return 4
            case MinorArcanaRank.FIVE:
                return 5
            case MinorArcanaRank.SIX:
                return 6
            case MinorArcanaRank.SEVEN:
                return 7
            case MinorArcanaRank.EIGHT:
                return 8
            case MinorArcanaRank.NINE:
                return 9
            case MinorArcanaRank.TEN:
                return 10
            case MinorArcanaRank.PAGE:
                return 11
            case MinorArcanaRank.KNIGHT:
                return 12
            case MinorArcanaRank.QUEEN:
                return 13
            case MinorArcanaRank.KING:
                return 14

    @typing.override
    def __str__(self) -> str:
        rank = f"[white]{self.value}[/white]"
        if self != MinorArcanaRank.TEN:
            rank = f"[bright_black]⋅[/bright_black]{rank}"
        return rank


class MinorArcanaSuit(enum.StrEnum):
    COINS = "🪙"  # U+1FA99
    CUPS = "🍷"  # U+1F377
    SWORDS = "🗡"  # U+1F5E1
    WANDS = "🪵"  # U+1FAB5

    @typing.override
    def __str__(self) -> str:
        fix = " " if self is MinorArcanaSuit.SWORDS else ""
        match self:
            case MinorArcanaSuit.COINS:
                color = "gold3"
            case MinorArcanaSuit.CUPS:
                color = "dark_orange3"  # "orange_red1"
            case MinorArcanaSuit.SWORDS:
                color = "steel_blue"
            case MinorArcanaSuit.WANDS:
                color = "yellow"  # "wheat4"
        return f"[{color}]{self.value}[/{color}]{fix}"


@dataclasses.dataclass  # (frozen=True)
class MinorArcana(Card[MinorArcanaRank, MinorArcanaSuit]):
    orientation: Orientation
    _rank: MinorArcanaRank = dataclasses.field(init=True, repr=False)
    _suit: MinorArcanaSuit = dataclasses.field(init=True, repr=False)

    @typing.override
    def __str__(self) -> str:
        return f"{self.rank!s}{self.suit!s}{self.orientation!s}"


MAJOR_ARCANA: collections.abc.Sequence[MajorArcana] = tuple(
    MajorArcana(
        _rank=rank,
        _suit=MajorArcanaSuit.MAJOR_ARCANA,
        orientation=Orientation.NORMAL,
    )
    for rank in MajorArcanaRank
)


MINOR_ARCANA: collections.abc.Sequence[MinorArcana] = tuple(
    MinorArcana(_rank=rank, _suit=suit, orientation=Orientation.NORMAL)
    for suit in MinorArcanaSuit
    for rank in MinorArcanaRank
)


type TarotDeck = collections.abc.Sequence[MajorArcana | MinorArcana]
ALL_CARDS: TarotDeck = tuple(itertools.chain(MAJOR_ARCANA, MINOR_ARCANA))
