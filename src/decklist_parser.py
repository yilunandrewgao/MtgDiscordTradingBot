from dataclasses import dataclass
from enum import Enum
import parsy


class Printing(Enum):
    Normal = "normal"
    Foil = "foil"
    EtchedFoil = "etched"


@dataclass
class CardQuery:
    name: str
    set_code: str | None = None
    collector_number: str | None = None
    printing: Printing = Printing.Normal


_space = parsy.regex(r' +')
_quantity = parsy.regex(r'\d+').map(int)
_set_code = parsy.string('(') >> parsy.regex(r'\w+') << parsy.string(')')
_collector_number = parsy.regex(r'[\w★\-]+')
_foil = parsy.string('*E*').result(Printing.EtchedFoil) | parsy.string('*F*').result(Printing.Foil)
_name = parsy.regex(r'[^(\n*]+').map(str.strip)


@parsy.generate
def _set_info():
    yield _space.optional()
    sc = yield _set_code
    cn = yield (_space >> _collector_number).optional()
    return (sc, cn)


@parsy.generate
def _card():
    yield _quantity
    yield _space
    n = yield _name
    si = yield _set_info.optional()
    sc, cn = si if si else (None, None)
    pr = yield (_space.optional() >> _foil).optional(Printing.Normal)
    return CardQuery(n, sc, cn, pr)


# Anything that isn't a card: consume the rest of the line as None
_skip_line = parsy.regex(r'[^\n]*').result(None)

_line = _card | _skip_line

_decklist = _line.sep_by(parsy.string('\n')).map(
    lambda cards: [c for c in cards if c is not None]
) << parsy.eof


def parse_decklist(text: str) -> list[CardQuery]:
    return _decklist.parse(text)
