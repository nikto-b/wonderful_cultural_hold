from __future__ import annotations
from dataclasses import dataclass
from typing import Union
from alphabet_detector import AlphabetDetector

SYMBOL = Union[str, 'Nonterminal']
ad = AlphabetDetector()


@dataclass(frozen=True)
class Nonterminal:
    symbol: str

    @classmethod
    def from_string(cls, s: str) -> SYMBOL:
        s = s.strip()
        if s.isupper() or (s[0].isalpha() and ad.is_greek(s[0])):
            return Nonterminal(s)
        return s

    def __repr__(self):
        return self.symbol


EPSYLON_SYMBOL = Nonterminal('ε')
