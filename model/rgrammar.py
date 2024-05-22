from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Generic, TypeVar

from model.nterm import Nonterminal, EPSYLON_SYMBOL
from model.rproduction import RProduction, ProductionCombination


@dataclass(frozen=True)
class RGrammar:
    _start: Nonterminal
    _productions: list[RProduction]

    @property
    def start(self) -> Nonterminal:
        return self._start

    @property
    def productions(self) -> list[RProduction]:
        return self._productions.copy()

    def productions_by_lhs(self, lhs: Nonterminal) -> ProductionCombination:
        ret = []
        for p in self._productions:
            if p.lhs == lhs:
                ret.append(p.rule)
        return ProductionCombination(lhs, ret)

    @classmethod
    def fromstring(cls, s: str, start: Optional[Nonterminal] = None) -> RGrammar:
        productions = list()
        start = None
        for line in s.split('\n'):
            line = line.strip()
            if len(line) == 0:
                continue

            p_s = RProduction.from_string(line)
            if start is None:
                start = p_s[0].lhs
            for p in p_s:
                productions.append(p)

        if start is None:
            start = Nonterminal('S')
            productions = [RProduction.from_string('S -> ε')]

        return RGrammar(start, productions)

    @property
    def nterms(self) -> list[Nonterminal]:
        ret = []

        for p in self._productions:
            if p.lhs not in ret:
                ret.append(p.lhs)

        for p in self._productions:
            if p.rule.nterm is not None and p.rule.nterm not in ret:
                ret.append(p.rule.nterm)

        return ret

    def copy_with(self,
                  start: Optional[Nonterminal] = None,
                  productions: Optional[list[RProduction]] = None) -> RGrammar:

        return RGrammar(start or self.start, productions or self.productions)
