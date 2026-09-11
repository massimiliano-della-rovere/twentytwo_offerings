import dataclasses

from twentytwo_offerings.can_be_sent_back import CAN_BE_SENT_BACK
from twentytwo_offerings.deck import MajorArcanaRank
from twentytwo_offerings.effects import EFFECTS, Effect
from twentytwo_offerings.rituals import RITUALS, Ritual


@dataclasses.dataclass(frozen=True)
class CardData:
    can_be_sent_back: bool
    effect: Effect | None
    ritual: Ritual


CARD_DATA: dict[MajorArcanaRank, CardData] = {
    major_arcana_rank: CardData(
        can_be_sent_back=CAN_BE_SENT_BACK[major_arcana_rank],
        effect=EFFECTS[major_arcana_rank],
        ritual=RITUALS[major_arcana_rank],
    )
    for major_arcana_rank in MajorArcanaRank
}
