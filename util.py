from typing import Union, Optional, Callable, Iterable

from model.rgrammar import RGrammar
from model.nterm import Nonterminal
from model.rproduction import RProduction


def productions_lhs(grammar: Union[RGrammar, Iterable[RProduction]], nterm: Nonterminal,
                    filter_func: Optional[Callable] = None) -> set[RProduction]:
    ret = set()

    if isinstance(grammar, RGrammar):
        productions = grammar.productions
    else:
        productions = set(grammar)

    for p in productions:
        if p.lhs == nterm:
            ret.add(p)

    if filter_func is None:
        return ret
    return set(filter(filter_func, ret))


def repr_grammar(grammar: Union[RGrammar, Iterable[RProduction]],
                 prefix='',
                 postfix='',
                 end='\n',
                 arrow_sep='\t-> ',
                 eq_sep=' | ') -> str:
    ret = ''
    for nterm in grammar.nterms:
        productions = grammar.productions_by_lhs(nterm)
        if len(productions.rhs_variants) == 0:
            continue

        ret += prefix + str(productions) + postfix
        ret += end

    return ret


def print_grammar(grammar: Union[RGrammar, Iterable[RProduction]],
                  prefix='',
                  postfix='',
                  end='\n',
                  arrow_sep='\t-> ',
                  eq_sep=' | ') -> None:
    print(repr_grammar(grammar, prefix, postfix, end, arrow_sep, eq_sep))
