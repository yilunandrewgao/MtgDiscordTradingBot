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

    def to_moxfield_query(self) -> str:
        parts = [self.name]
        if self.set_code:
            parts.append(f'set:{self.set_code}')
        if self.collector_number:
            parts.append(f'number:{self.collector_number}')
        return f'({" ".join(parts)})'


_space = parsy.regex(r' +')
_quantity = parsy.regex(r'\d+').map(int)
_set_code = parsy.string('(') >> parsy.regex(r'\w+') << parsy.string(')')
_collector_number = parsy.regex(r'[\w★\-]+')
_foil = parsy.string('*E*').result(Printing.EtchedFoil) | parsy.string('*F*').result(Printing.Foil)
_name = parsy.regex(r'[^(\n*\|]+').map(str.strip)


@parsy.generate
def _set_info():
    yield _space.optional()
    sc = yield _set_code
    cn = yield (_space >> _collector_number).optional()
    return (sc, cn)


@parsy.generate
def _moxfield_card():
    yield _quantity
    yield _space
    n = yield _name
    si = yield _set_info.optional()
    sc, cn = si if si else (None, None)
    pr = yield (_space.optional() >> _foil).optional(Printing.Normal)
    return CardQuery(n, sc, cn, pr)


@parsy.generate
def _legacy_card():
    n = yield _name
    si = yield _set_info.optional()
    sc, cn = si if si else (None, None)
    pr = yield (_space.optional() >> _foil).optional(Printing.Normal)
    return CardQuery(n, sc, cn, pr)


_newlines = parsy.regex(r'\n+')

_moxfield_decklist = _moxfield_card.sep_by(_newlines) << parsy.eof

_legacy_decklist = _legacy_card.sep_by(parsy.regex(r' *[\|\n] *')) << parsy.eof

_decklist = _moxfield_decklist | _legacy_decklist


def parse_decklist(text: str) -> list[CardQuery]:
    cleaned = "\n".join(
        line for line in text.splitlines()
        if not line.strip().startswith("@")
    )
    return _decklist.parse(cleaned)
