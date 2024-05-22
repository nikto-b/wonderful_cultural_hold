from __future__ import annotations
from dataclasses import dataclass
from typing import Union, Iterable, Optional

from model.nterm import Nonterminal, SYMBOL
from model.production import ABCProduction


@dataclass(frozen=True)
class RProductionRule:
    terms: tuple[str, ...]
    nterm: Optional[Nonterminal]

    def combined(self) -> tuple[SYMBOL, ...]:
        return self.terms + ((self.nterm,) if self.nterm is not None else tuple())

    def __repr__(self) -> str:
        ret = ' '.join(self.terms)
        if self.nterm is not None:
            ret += ' ' + str(self.nterm)
        return ret


@dataclass(frozen=True)
class RProduction(ABCProduction):
    _lhs: Nonterminal
    _rhs: RProductionRule

    @classmethod
    def from_string(cls, s: str) -> list[RProduction]:
        lhs, tail = s.split('->')
        rhs_s = tail.split('|')

        ret = []
        for rhs_str in rhs_s:
            terms = tuple(map(Nonterminal.from_string, rhs_str.split()))
            nterm = terms[-1]
            if isinstance(nterm, Nonterminal):
                terms = terms[:-1]
            else:
                nterm = None
            rules = RProductionRule(terms, nterm)
            p = RProduction(Nonterminal.from_string(lhs), rules)
            ret.append(p)
        return ret

    @classmethod
    def repr_multiple(cls, productions: Iterable[RProduction], arrow_sep='\t-> ', eq_sep=' | ') -> str:
        productions = list(productions)
        return (productions[0].lhs.symbol + arrow_sep +
                eq_sep.join(map(lambda p: ' '.join(map(str, p.rhs)), productions)))

    def __repr__(self):
        return f'{self.lhs} -> ' + ' '.join(self._rhs.terms) + ' ' + str(self._rhs.nterm)

    @property
    def rhs(self) -> tuple[SYMBOL, ...]:
        return self._rhs.combined()

    @property
    def lhs(self) -> Nonterminal:
        return self._lhs

    @property
    def rule(self) -> RProductionRule:
        return self._rhs


@dataclass
class ProductionCombination:
    lhs: Nonterminal
    rhs_variants: list[RProductionRule]

    def __repr__(self) -> str:
        ret = f'{self.lhs} ->'
        ret += ' | '.join(map(str, self.rhs_variants))
        return ret
