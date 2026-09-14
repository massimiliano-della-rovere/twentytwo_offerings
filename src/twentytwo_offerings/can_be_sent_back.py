# from twentytwo_offerings.deck import MajorArcanaRank
from twentytwo_offerings.deck_with_orientation import MajorArcanaRank

CAN_BE_SENT_BACK: dict[MajorArcanaRank, bool] = {
    MajorArcanaRank.FOOL: True,
    MajorArcanaRank.MAGICIAN: True,
    MajorArcanaRank.HIGH_PRIESTESS: True,
    MajorArcanaRank.EMPRESS: True,
    MajorArcanaRank.EMPEROR: True,
    MajorArcanaRank.HIEROPHANT: True,
    MajorArcanaRank.LOVERS: True,
    MajorArcanaRank.CHARIOT: True,
    MajorArcanaRank.JUSTICE: True,
    MajorArcanaRank.HERMIT: True,
    MajorArcanaRank.WHEEL_OF_FORTUNE: True,
    MajorArcanaRank.STRENGTH: True,
    MajorArcanaRank.HANGED_MAN: True,
    MajorArcanaRank.DEATH: True,
    MajorArcanaRank.TEMPERANCE: True,
    MajorArcanaRank.DEVIL: False,
    MajorArcanaRank.TOWER: True,
    MajorArcanaRank.STAR: True,
    MajorArcanaRank.MOON: True,
    MajorArcanaRank.SUN: True,
    MajorArcanaRank.JUDGEMENT: True,
    MajorArcanaRank.WORLD: True,
}
