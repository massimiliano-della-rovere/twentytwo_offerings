from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import cycle
from typing import Callable, Protocol, overload, runtime_checkable

import rich.console

CONSOLE = rich.console.Console(highlight=False)


class Glyphs(StrEnum):
    # \ufe0e =? Do not render Unicode charactes as glyphs
    GE = "≥\ufe0e"
    LE = "≤\ufe0e"
    OPEN_CHEVRONS = "«\ufe0e"
    CLOSE_CHEVRONS = "»\ufe0e"
    THICK_DASH = "━\ufe0e"
    TRIANGLE_UP = "▴\ufe0e"
    TRIANGLE_DOWN = "▾\ufe0e"
    SMALL_DOT = "⋅\ufe0e"
    MID_DOT = "·\ufe0e"
    MID_X = "×\ufe0e"
    PARAGRAPH = "§\ufe0e"
    IDENTITY = "≡\ufe0e"
    ID_CARD = "🪪\ufe0e"
    LABEL = "🏷️\ufe0e"
    EDIT = "📝\ufe0e"
    TEXT = "🗒️\ufe0e"
    EYE = "👁\ufe0e"
    EYES = "👀\ufe0e"
    HOURGLASS = "⌛\ufe0e"
    BOX = "📦\ufe0e"
    CART = "🛒\ufe0e"
    COIN = "🪙\ufe0e"
    SKULL = "☠ \ufe0e"
    WARNING = "⚠ \ufe0e"
    PLACE_OF_INTEREST = "⌘\ufe0e"
    PUSHPIN = "📍\ufe0e"
    PIN = "📌\ufe0e"
    MAP = "🗺️\ufe0e"
    KEY = "🔑\ufe0e"
    KEY_OLD = "🗝\ufe0e"
    LOCK_CLOSED_WITH_KEY = "🔐\ufe0e"
    LOCK_CLOSED = "🔒\ufe0e"
    LOCK_OPEN = "🔓\u0f0e"
    POSITION = "⌖\ufe0e"
    STAR_FILLED = "★\ufe0e"
    STAR_EMPTY = "☆\ufe0e"
    STAR_CIRCLE = "✪\ufe0e"
    INFINITY = "∞\ufe0e"
    ESC = "⎋\ufe0e"
    EMPTY = "∅\ufe0e"
    DOUBLE_EXCLAMATION = "‼\ufe0e"
    PROHIBITED = "🛇\ufe0e"
    SPARKLE = "🞢\ufe0e"
    CROSS = "✘\ufe0e"
    INFO = "🛈\ufe0e"
    PROMPT = "❯\ufe0e"
    CHECK = "🗸\ufe0e"
    ENTER = "↵\ufe0e"
    SPRING = "🌸\ufe0e"
    SUMMER = "☀ \ufe0e"
    AUTUMN = "🍁\ufe0e"
    WINTER = "❄ \ufe0e"
    WEEK = "📅\ufe0e"
    MONTH = "🌙\ufe0e"
    YEAR = "🌍\ufe0e"
    D_ELLIPSIS = "∵\ufe0e"
    H_ELLIPSIS = "…\ufe0e"
    M_ELLIPSIS = "⋯\ufe0e"
    S_ELLIPSIS = "⁖\ufe0e"
    U_ELLIPSIS = "∴\ufe0e"
    V_ELLIPSIS = "⋮\ufe0e"


COMPOSITE_CHOICE_SEPARATOR = "#"

INPUT_CHOICE_INDEXES = (
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
)


def input_choice_enumerate[T](iterable: Iterable[T]) -> Iterator[tuple[str, T]]:
    yield from zip(INPUT_CHOICE_INDEXES, iterable)


class AddChoicesSharedTextToPrompt(Protocol):
    def __call__(self, choices_answer: str, indent: int) -> None: ...


@runtime_checkable
class InputChoicesValidator(Protocol):
    def __call__(
        self,
        selected_items: frozenset[str],
        dynamic_text: dict[str, str],
    ) -> bool: ...


@runtime_checkable
class InputChoicesEvent(Protocol):
    def __call__(
        self,
        answer: str,
        dynamic_text: dict[str, str],
    ) -> None: ...


@runtime_checkable
class InputResultValidator(Protocol):
    def __call__(self, answer: str) -> bool: ...


type Groups = dict[str, Sequence[str]]


@dataclass  # (frozen=True)
class InputParams:
    title: str
    text: str
    groups: Groups = field(default_factory=dict)

    result_validator: InputResultValidator | None = None

    choices: dict[str, str] = field(default_factory=dict)
    choices_min: int = 1
    choices_max: int = 1
    choices_shared_text: dict[str, str] = field(default_factory=dict)
    choices_shared_text_allow_sparse: bool = False
    choices_validator: InputChoicesValidator | None = None
    choices_before_add: InputChoicesEvent | None = None
    choices_after_remove: InputChoicesEvent | None = None


class Input:
    def __init__(self) -> None:
        self._inverted_translation_table: dict[str, str] = dict()
        self._selected_items: set[str] = set()
        self._prompt: list[str] = list()
        self._raw_answer_validator: Callable[[str], bool]
        self._raw_answer_converter: Callable[[str], str]
        self._translation_table: dict[str, str]
        self._additional_dynamic_text: dict[str, str] = {}

        self._params: InputParams
        self._input_engine: Callable[[], None]

    def _input_choices_validate(self) -> None:
        if self._params.choices_min < 0:
            raise ValueError(f"choices_min must be {Glyphs.GE} 0.")

        if self._params.choices_min > len(self._params.choices):
            raise ValueError(f"choices_min must be {Glyphs.LE} len(choices).")

        if -1 < self._params.choices_max < self._params.choices_min:
            raise ValueError(
                f"choices_max must be -1 or {Glyphs.GE} choices_min."
            )

    def _input_choices_quick_result(self) -> None | str:
        if len(self._params.choices) == 1:
            return next(iter(self._params.choices))

        if len(self._params.choices) == self._params.choices_max:
            return "\n".join(self._params.choices)

    def _update_translation_table_and_selected_items(
        self,
        idx: str,
        key: str,
        indent: int,
    ) -> None:
        if indent < 0:
            raise ValueError("Param indent must be > 0.")

        self._translation_table[idx] = key
        text = self._params.choices[key]  # .replace("\t", "\t\t")
        if key in self._selected_items:
            symbol = f"[red]{Glyphs.CROSS}[/red]"
        elif len(self._selected_items) < self._params.choices_max:
            symbol = f"[green]{Glyphs.SPARKLE}[/green]"
        else:
            return

        try:
            value = self._additional_dynamic_text[key]
        except KeyError:
            extra = ""
        else:
            extra = (
                f" [bright_white bold]{Glyphs.IDENTITY}[/bright_white bold]"
                f" [plum1]{value}[/plum1]"
            )
        self._prompt.append(
            (
                f"{"\t" * indent}"
                f"[bright_black]{Glyphs.CLOSE_CHEVRONS}[/bright_black]"
                f"[bright_white]{idx}[/bright_white]"
                f"[bright_black]{Glyphs.OPEN_CHEVRONS} ::[/bright_black]"
                f" {symbol} {text}{extra}"
            )
        )

    def _can_confirm_selection(self) -> bool:
        return self._params.choices_min <= len(
            self._selected_items
        ) <= self._params.choices_max and (
            not callable(self._params.choices_validator)
            or self._params.choices_validator(
                selected_items=frozenset(self._selected_items),
                dynamic_text=self._additional_dynamic_text,
            )
        )

    def _add_selected_items_or_confirm_selection(self) -> None:
        if self._params.choices_shared_text:
            selected_items = tuple(
                (
                    f"[bright_black]{Glyphs.CLOSE_CHEVRONS}[/bright_black]"
                    f"[bright_white]"
                    f"{self._inverted_translation_table[selected_item]}"
                    f"[/bright_white]"
                    f"[bright_black]{Glyphs.OPEN_CHEVRONS}[/bright_black]"
                )
                for selected_item in self._selected_items
            )
        else:
            selected_items = self._selected_items

        if self._params.choices_max > 0:
            self._prompt.append(
                (
                    f"[light_cyan1]{Glyphs.CART}[/light_cyan1]"
                    f" {", ".join(sorted(selected_items))}"
                )
            )
        if self._can_confirm_selection():
            self._translation_table["."] = "."
            self._prompt.append(
                (
                    f"\t"
                    f"[bright_black]{Glyphs.CLOSE_CHEVRONS}[/bright_black]"
                    f"[bright_white].[/bright_white]"
                    f"[bright_black]{Glyphs.OPEN_CHEVRONS} ::[/bright_black]"
                    f" [light_sea_green]{Glyphs.ESC}[/light_sea_green]"
                    f" & [light_sea_green]{Glyphs.ENTER}[/light_sea_green]"
                    f" {", ".join(sorted(selected_items))}"
                )
            )

    def _validate_shared_text_vs_groups(self) -> None:
        tester: defaultdict[str, list[str]] = defaultdict(list)

        for group_name, choices_answers in self._params.groups.items():
            for choices_answer in choices_answers:
                answer_shared_root = choices_answer.split(
                    COMPOSITE_CHOICE_SEPARATOR
                )[0]
                tester[answer_shared_root].append(group_name)

        if errors := {
            f"{answer_shared_root}: {", ".join(groups)}"
            for answer_shared_root, groups in tester.items()
            if len(groups) > 1
        }:
            raise ValueError(
                (
                    f"The following shared roots from the choices parameter"
                    f" were found in multiple groups: {"; ".join(errors)}."
                )
            )

    def _choices_shared_text_dispenser(self) -> AddChoicesSharedTextToPrompt:
        current_answer_shared_root = ""

        def _add_choices_shared_text_to_prompt(
            choices_answer: str,
            indent: int,
        ) -> None:
            nonlocal current_answer_shared_root

            if indent < 0:
                raise ValueError("Param indent must be > 0.")

            if not self._params.choices_shared_text:
                return

            answer_shared_root = choices_answer.split(
                COMPOSITE_CHOICE_SEPARATOR
            )[0]
            if answer_shared_root == current_answer_shared_root:
                return

            current_answer_shared_root = answer_shared_root
            try:
                text = self._params.choices_shared_text[answer_shared_root]
            except KeyError:
                return

            self._prompt.append(f"{"\t" * indent}{text}")

        return _add_choices_shared_text_to_prompt

    def _add_choices_items(self):
        choices_shared_text_dispenser = self._choices_shared_text_dispenser()

        if self._params.groups:
            if (
                self._params.choices_shared_text
                and not self._params.choices_shared_text_allow_sparse
            ):
                self._validate_shared_text_vs_groups()

            enumerator = cycle(INPUT_CHOICE_INDEXES)
            for group_name, choices_answers in self._params.groups.items():
                if not choices_answers:
                    continue

                self._prompt.append(
                    (
                        f"[bright_white bold]{Glyphs.MID_DOT}"
                        f"[/bright_white bold] {group_name}"
                    )
                )
                for choices_answer in sorted(choices_answers):
                    choices_shared_text_dispenser(
                        choices_answer=choices_answer, indent=1
                    )
                    self._update_translation_table_and_selected_items(
                        idx=next(enumerator),
                        key=choices_answer,
                        indent=2,
                    )
        else:
            for idx, choices_answer in input_choice_enumerate(
                sorted(self._params.choices)
            ):
                choices_shared_text_dispenser(
                    choices_answer=choices_answer,
                    indent=0,
                )
                self._update_translation_table_and_selected_items(
                    idx=idx,
                    key=choices_answer,
                    indent=1,
                )

    def _make_choices_prompt_validator_converter(self) -> None:
        self._translation_table = {}

        self._prompt = [
            self._params.title.upper(),
            "=" * len(self._params.title),
        ]

        if self._params.text:
            self._prompt.append(self._params.text)

        self._add_selected_items_or_confirm_selection()

        self._add_choices_items()

        self._prompt.append(
            (
                f"[light_cyan1][italic]{Glyphs.INFO}"
                f" {self._params.choices_min}-{self._params.choices_max}"
                f"[/italic] {Glyphs.PROMPT}[/light_cyan1] "
            )
        )

        self._raw_answer_validator = self._translation_table.__contains__
        self._raw_answer_converter = self._translation_table.__getitem__

        self._inverted_translation_table = {
            choices_answer: idx
            for idx, choices_answer in self._translation_table.items()
        }

    def _make_simple_question_prompt_validator_converter(self) -> None:
        self._prompt = [
            self._params.title.upper(),
            "=" * len(self._params.title),
        ]
        if self._params.text:
            self._prompt.append(self._params.text)

        for group_name, paragraphs in self._params.groups.items():
            if not paragraphs:
                continue

            self._prompt.append(
                (
                    f"[bright_white bold]{Glyphs.MID_DOT}[/bright_white bold]"
                    f" {group_name}"
                )
            )
            for paragraph in paragraphs:
                self._prompt.append(f"\t{paragraph.replace("\n", "\n\t")}")
        self._prompt.append(f"[light_cyan1]{Glyphs.PROMPT}[/light_cyan1] ")

        self._raw_answer_validator = bool
        self._raw_answer_converter = str

    def _preprocess_raw_answer(self, raw_answer: str) -> str:
        ret = raw_answer.strip()
        if self._params.choices:
            ret = ret.rstrip("!")
        return ret

    def _output_error(self, text: str) -> None:
        CONSOLE.print(
            (
                f"[bright_red]{Glyphs.DOUBLE_EXCLAMATION}[/bright_red]"
                f" {repr(text)}\n\n"
            )
        )

    def _output_accepted(self, text: str) -> None:
        CONSOLE.print(
            (
                f"[bright_green bold]{Glyphs.CHECK}[/bright_green bold]"
                f" {text}\n\n"
            )
        )

    def _get_user_answer(self) -> str:
        while True:
            self._input_engine()
            raw_answer = CONSOLE.input("\n".join(self._prompt))

            if not self._raw_answer_validator(
                self._preprocess_raw_answer(raw_answer)
            ):
                self._output_error(raw_answer)
                continue

            if self._params.choices:
                if self._process_choices_raw_answer(raw_answer):
                    return "\n".join(self._selected_items)
            else:
                if callable(
                    self._params.result_validator
                ) and not self._params.result_validator(raw_answer):
                    self._output_error(raw_answer)
                    continue

                answer = self._raw_answer_converter(raw_answer)
                self._output_accepted(answer)
                return answer

    def _process_choices_raw_answer(self, raw_answer: str) -> bool:
        if raw_answer[-1] == "!":
            raw_answer = raw_answer[:-1]
            force_return = True
        else:
            force_return = raw_answer == "."

        answer = self._raw_answer_converter(raw_answer)

        if force_return:
            if answer != ".":
                self._selected_items.add(answer)

            CONSOLE.print(
                f"[bright_green]{Glyphs.CHECK}[/bright_green] {answer}"
            )
            if self._can_confirm_selection():
                CONSOLE.print(
                    (
                        f"[light_sea_green]{Glyphs.ENTER}[/light_sea_green]"
                        f" {", ".join(self._selected_items)}\n\n"
                    )
                )
                return True

        if answer in self._selected_items:
            CONSOLE.print("")
            self._selected_items.remove(answer)
            if callable(self._params.choices_after_remove):
                self._params.choices_after_remove(
                    answer=answer,
                    dynamic_text=self._additional_dynamic_text,
                )
        else:
            if callable(self._params.choices_before_add):
                self._params.choices_before_add(
                    answer=answer,
                    dynamic_text=self._additional_dynamic_text,
                )
            self._selected_items.add(answer)

        return False

    def __call__(self, input_params: InputParams) -> str:
        self._selected_items = set()
        self._params = input_params

        if input_params.choices:
            # TODO: choices_common_text
            self._input_choices_validate()

            if ret := self._input_choices_quick_result():
                return ret

            if input_params.choices_max == -1:
                self._params = self._params.__replace__(
                    choices_max=len(input_params.choices),
                )

            self._input_engine = self._make_choices_prompt_validator_converter
        else:
            self._input_engine = (
                self._make_simple_question_prompt_validator_converter
            )

        return self._get_user_answer()


@overload
def ask[T](
    title: str,
    text: str,
    result_caster: Callable[[str], T],
    result_validator: InputResultValidator | None = None,
    groups: Groups | None = None,
    choices: dict[str, str] | None = None,
    choices_min: int = 1,
    choices_max: int = 1,
    choices_shared_text: dict[str, str] | None = None,
    choices_shared_text_allow_sparse: bool = False,
    choices_validator: InputChoicesValidator | None = None,
    choices_before_add: InputChoicesEvent | None = None,
    choices_after_remove: InputChoicesEvent | None = None,
) -> T: ...


@overload
def ask(
    title: str,
    text: str,
    result_caster: None = None,
    result_validator: InputResultValidator | None = None,
    groups: Groups | None = None,
    choices: dict[str, str] | None = None,
    choices_min: int = 1,
    choices_max: int = 1,
    choices_shared_text: dict[str, str] | None = None,
    choices_shared_text_allow_sparse: bool = False,
    choices_validator: InputChoicesValidator | None = None,
    choices_before_add: InputChoicesEvent | None = None,
    choices_after_remove: InputChoicesEvent | None = None,
) -> str: ...


def ask[T](
    title: str,
    text: str,
    result_caster: Callable[[str], T] | None = None,
    result_validator: InputResultValidator | None = None,
    groups: Groups | None = None,
    choices: dict[str, str] | None = None,
    choices_min: int = 1,
    choices_max: int = 1,
    choices_shared_text: dict[str, str] | None = None,
    choices_shared_text_allow_sparse: bool = False,
    choices_validator: InputChoicesValidator | None = None,
    choices_before_add: InputChoicesEvent | None = None,
    choices_after_remove: InputChoicesEvent | None = None,
) -> str | T:
    input_params = InputParams(
        title=title,
        text=text,
        groups=groups or {},
        result_validator=result_validator,
        choices=choices or {},
        choices_min=choices_min,
        choices_max=choices_max,
        choices_shared_text=choices_shared_text or {},
        choices_shared_text_allow_sparse=choices_shared_text_allow_sparse,
        choices_validator=choices_validator,
        choices_before_add=choices_before_add,
        choices_after_remove=choices_after_remove,
    )
    ask = Input()
    result = ask(input_params=input_params)

    if callable(result_caster):
        result = result_caster(result)

    return result


def output(
    title: str,
    text: str | None = None,
    groups: dict[str, Sequence[str]] | None = None,
) -> None:
    parts: list[str] = [title.upper(), "=" * len(title)]

    if text:
        parts.append(text)

    if groups:
        for group_name, paragraphs in groups.items():
            parts.append(
                (
                    f"[bright_white bold]{Glyphs.MID_DOT}[/bright_white bold]"
                    f" {group_name}"
                )
            )
            for paragraph in paragraphs:
                parts.append(f"\t{paragraph.replace("\n", "\n\t")}")

    if text is None and groups is None:
        raise ValueError("Either text or groups must be not None.")

    params = "\n".join(parts)

    CONSOLE.print(f"{params}\n")
