from __future__ import annotations

import string
from dataclasses import dataclass
from typing import Union, Any, Optional

from eq_solver import Expr, Elem, Closure, Item
from model.rgrammar import RGrammar
from model.nterm import Nonterminal, SYMBOL
import numpy as np

from model.rproduction import ProductionCombination
from regex_solver import RegexEquation, regex_solve
from util import print_grammar


def input_grammar() -> str:
    # print('Pass grammar. End with `EOF`')
    grammar_string = ''
    # while (line := input()) != 'EOF':
    #     grammar_string += line + '\n'
    if len(grammar_string) == 0:
        # (A | B) * ABB

        return '''
            S -> a S | b S | a b b | a b b
        '''

        # return '''
        #         X1 -> 0 X2 | 1 X1 | ε
        #         X2 -> 0 X3 | 1 X2
        #         X3 -> 0 X1 | 1 X3
        #         '''
    return grammar_string


@dataclass
class FSM:
    start_state: str
    states: dict[str, FSMState]

    def __init__(self, start_state: str, states: list[FSMState]):
        self.start_state = start_state
        self.states = {}
        for state in states:
            if state.name in self.states.keys():
                raise RuntimeError(f'Got duplicate state "{state.name}" in a FSM constructor')
            self.states[state.name] = state
        if start_state not in self.states.keys():
            raise RuntimeError(f'No start state "{start_state}" provided in a FSM')
        for state in self.states.values():
            for rib in state.ribs:
                if rib.state_name not in self.states.keys():
                    raise RuntimeError(f'No state "{rib.state_name}" found, but referenced from "{state.name}"')

    def state_by_name(self, name: str) -> FSMState:
        return self.states[name]

    def apply(self, chain: str, trace: Optional[FSMTrace] = None) -> (bool, FSMState, FSMTrace):
        if trace is None:
            trace = FSMTrace([self.start_state])

        last_item = self.state_by_name(trace.last)

        if len(last_item.ribs) == 0 and len(chain) == 0:
            return True, last_item, trace

        # trace = trace.add(last_item.name)

        ribs = []
        for rib in last_item.ribs:
            if rib.can_apply(chain):
                ribs.append(rib)
        if len(ribs) == 0:
            return False, self, trace

        for rib in ribs:
            lookup_state = self.state_by_name(rib.state_name)
            apply_chain = chain
            if rib.symbol is not None:
                apply_chain = apply_chain[1:]
            result, result_state, new_trace = self.apply(apply_chain, trace.add(lookup_state.name))
            if result:
                return True, result_state, new_trace
        return False, self, trace

    @staticmethod
    def _sanitize_mermaid(s: str) -> str:
        if s == 'end':
            return '__end'
        return s.replace('.', '_').replace('*', '__')

    def as_mermaid(self) -> str:
        lines = ['flowchart LR']
        for state in self.states.values():
            idx = self._sanitize_mermaid(state.name)
            name = state.name
            if name.endswith('.start') or name.endswith('.end'):
                name = ' '
            lines.append(f'\t{idx}(("{name}"))')

        for state in self.states.values():
            idx = self._sanitize_mermaid(state.name)
            for rib in state.ribs:
                arrow = '-->'
                if rib.symbol is not None:
                    arrow = f' -- "{rib.symbol}" -->'
                lines.append(
                    f'\t{idx} {arrow} {self._sanitize_mermaid(rib.state_name)}')

        return '\n'.join(lines)


@dataclass
class FSMTrace:
    items: list[str]

    def add(self, item: str) -> FSMTrace:
        return FSMTrace(self.items + [item])

    @property
    def last(self):
        return self.items[-1]


class FSMState:
    name: str
    ribs: list[FSMRib]

    def __init__(self, name: str, ribs: Optional[list[FSMRib]] = None):
        self.name = name
        self.ribs = ribs or []

    def add_ribs(self, ribs: list[FSMRib]) -> FSMState:
        return FSMState(self.name, self.ribs + ribs)

    def replace_rib(self, what: FSMRib, replace: FSMRib) -> FSMState:
        new_ribs = []
        for rib in self.ribs:
            if rib == what:
                rib = replace
            new_ribs.append(rib)
        return self.set_ribs(new_ribs)

    def set_ribs(self, ribs: list[FSMRib]) -> FSMState:
        return FSMState(self.name, ribs)

    def __repr__(self) -> str:
        return f'State{{{self.name}}}'

    def __eq__(self, other):
        return isinstance(other, FSMState) and self.name == other.name

    def __hash__(self):
        return self.name.__hash__()


@dataclass
class FSMRib:
    symbol: Optional[str]
    state_name: str

    def can_apply(self, chain: str) -> bool:
        return self.symbol is None or (len(chain) > 0 and self.symbol == chain[0])


def char_from_idx(idx: int) -> str:
    idx -= 1
    letters = len(string.ascii_uppercase)
    ret = ''
    while idx < 0:
        idx += letters
    while idx > letters:
        ret += string.ascii_uppercase[-1]
        idx -= letters

    ret += string.ascii_uppercase[idx % letters]
    return ret


def fsm_from_closure(closure: Closure, prefix: str = '', end_ribs: Optional[list[FSMRib]] = None) -> list[FSMState]:
    start_state = FSMState(prefix + 'start')
    end_state = FSMState(prefix + 'end', end_ribs)
    states = []
    inner_states = fsm_from_item(closure.child, f'{prefix}*.',
                                 [FSMRib(None, end_state.name), FSMRib(None, f'{prefix}*.start')])

    start_state = start_state.add_ribs([FSMRib(None, inner_states[0].name), FSMRib(None, end_state.name)])
    return [start_state] + inner_states + [end_state]


def fsm_from_sum(expr: Expr, prefix: str = '', end_ribs: Optional[list[FSMRib]] = None) -> list[FSMState]:
    start_state = FSMState(prefix + 'start')
    end_state = FSMState(prefix + 'end', end_ribs)
    internal_end_ribs = [FSMRib(None, prefix + 'end')]
    states = []
    idx = 1
    for arg in expr.args:
        new_states = fsm_from_item(arg, f'{prefix}{char_from_idx(idx)}.', internal_end_ribs)
        start_state = start_state.add_ribs([FSMRib(None, f'{prefix}{char_from_idx(idx)}.start')])
        states += new_states
        idx += 1

    return [start_state] + states + [end_state]


def fsm_from_mul(expr: Expr, prefix: str = '', end_ribs: Optional[list[FSMRib]] = None) -> list[FSMState]:
    start_state = FSMState(prefix + 'start', [FSMRib(None, f'{prefix}{char_from_idx(1)}.start')])
    states: list[FSMState] = [start_state]
    idx = 1
    for arg in expr.args:
        internal_end_ribs = [FSMRib(None, f'{prefix}{char_from_idx(idx + 1)}.start')]
        new_states = fsm_from_item(arg,
                                   f'{prefix}{char_from_idx(idx)}.',
                                   internal_end_ribs)
        states += new_states
        idx += 1

    end_state = FSMState(f'{prefix}{char_from_idx(idx)}', end_ribs)
    states[-1] = states[-1].replace_rib(FSMRib(None, f'{prefix}{char_from_idx(idx)}.start'),
                                        FSMRib(None, end_state.name))
    return states + [end_state]


def fsm_from_elem(el: Elem,
                  prefix: str = '',
                  end_ribs: Optional[list[FSMRib]] = None) -> list[FSMState]:
    end_state = FSMState(prefix + 'end', end_ribs)

    sym = el
    if str(sym) == 'ε':
        sym = None
        state = FSMState(prefix + 'ε', [FSMRib(None, end_state.name)])
        start_state = FSMState(prefix + 'start', [FSMRib(None, state.name)])

    else:
        state = FSMState(prefix + sym.sym, [FSMRib(None, end_state.name)])
        start_state = FSMState(prefix + 'start', [FSMRib(sym.sym, state.name)])

    return [start_state, state, end_state]


def fsm_from_expression(expr: Expr, prefix: str = '', end_ribs: Optional[list[FSMRib]] = None) -> list[FSMState]:
    if expr.op.sym == '+':
        return fsm_from_sum(expr, prefix, end_ribs)
    elif expr.op.sym == '*':
        return fsm_from_mul(expr, prefix, end_ribs)
    else:
        raise RuntimeError(f'Unsupported operation: {expr.op}')


def fsm_from_item(item: Item, prefix: str = '', end_ribs: Optional[list[FSMRib]] = None) -> list[FSMState]:
    if isinstance(item, Elem):
        return fsm_from_elem(item, prefix, end_ribs)
    elif isinstance(item, Expr):
        return fsm_from_expression(item, prefix, end_ribs)
    elif isinstance(item, Closure):
        return fsm_from_closure(item, prefix, end_ribs)
    else:
        raise RuntimeError(f'Sun has been exploded (got {type(item)})')


def main():
    grammar = RGrammar.fromstring(input_grammar())

    print('Input grammar:')
    print_grammar(grammar)

    eqs: list[RegexEquation] = RegexEquation.expr_from_grammar(grammar)

    print('\nInput eqs: ')
    for eq in eqs:
        print(f'> {eq}')

    eqs = regex_solve(eqs)

    print('\nSolved eqs: ')
    for eq in eqs:
        print(f'> {eq}')

    interested_regex = list(filter(lambda x: x.X.sym == grammar.start, eqs))[0].calculate_result()

    print(f'Calculated regex: {interested_regex}\n')

    s = FSM('start', fsm_from_item(interested_regex))

    print(s)
    print()
    print(s.as_mermaid())

    print(f'Press <^D> for exit')
    while True:
        try:
            test_str = input('(try it out)> ')
        except EOFError:
            print('Exiting')
            break
        print(s.apply(test_str))
    # fsm = FSM(
    #     'start',
    #     [
    #         FSMState(
    #             'start',
    #             [FSMRib('a', 'a state')]
    #         ),
    #         FSMState('end'),
    #         FSMState(
    #             'a state',
    #             [
    #                 FSMRib('a', 'a state'),
    #                 FSMRib('b', 'b state'),
    #                 FSMRib(None, 'end'),
    #             ]
    #         ),
    #         FSMState(
    #             'b state',
    #             [
    #                 FSMRib(None, 'end')
    #             ]
    #         )
    #     ]
    # )

    # fsm = FSMState(
    #     'Start state',
    #     FSMRib(
    #         'a',
    #         FSMState(
    #             'State a',
    #             FSMRib(
    #                 'b',
    #                 FSMState('final b state')
    #             ),
    #             FSMRib(
    #                 'c',
    #                 FSMState('final c state')
    #             ),
    #         )
    #     )
    # )

    # print(fsm.apply('aaaaaaab'))

    # print(fsm.end_states())


if __name__ == '__main__':
    main()
