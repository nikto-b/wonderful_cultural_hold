from __future__ import annotations

from dataclasses import dataclass

from eq_solver import Expr, Elem, Closure, Item
from model.nterm import Nonterminal
from model.rgrammar import RGrammar
from model.rproduction import ProductionCombination


@dataclass
class RegexEquation:
    alpha: Expr
    X: Elem
    beta: Expr

    def calculate_result(self) -> Expr:
        """
        Преобразовывает αX+β => (α*)×β
        Уравнение 2.2.1 -- Ахо А., Ульман Дж. Теория синтаксического анализа, перевода и компиляции
        """
        return Expr('*', [Closure(self.alpha), self.beta]).flatten()

    def __repr__(self) -> str:
        return (f'RegexEquation('
                f'α={str(self.alpha).replace(" ", "")}, '
                f'X={self.X}, '
                f'β={str(self.beta).replace(" ", "")}'
                f')')

    def replace_beta(self, replace_what: Item, replace_with: Item) -> RegexEquation:
        return RegexEquation(self.alpha, self.X, self.beta.replace(replace_what, replace_with).flatten())

    @classmethod
    def from_expr(cls, expr: Expr, X: Elem):

        beta, extracted = expr.extract(X)

        alpha_els = []
        for e in extracted:
            if isinstance(e, Expr):
                e, new_e = e.extract(X)
                if len(new_e) > 1:
                    raise ValueError(f'Unable to extract {X} from equation {expr}')
            if e == X:
                e = Elem(Nonterminal('ε'))
            alpha_els.append(e)
        alpha = Expr('+', alpha_els).flatten()
        return RegexEquation(alpha, X, beta.flatten())

    def rearrange_X(self) -> RegexEquation:
        expr = Expr(
            '+',
            [
                Expr('*',
                     [
                         self.alpha,
                         self.X
                     ]),
                self.beta
            ]
        ).flatten()
        return self.from_expr(expr, self.X)

    @classmethod
    def expr_from_productions(cls, p: ProductionCombination) -> Expr:
        sum_with = []
        for variant in p.rhs_variants:
            els = variant.combined()
            if len(els) > 1:
                sum_with.append(Expr('*', list(map(lambda x: Elem(x), els))))
            elif len(els) == 1:
                sum_with.append(Elem(els[0]))

        return Expr('+', sum_with)

    @classmethod
    def expr_from_grammar(cls, g: RGrammar) -> list[RegexEquation]:
        eqs = []
        nterms = g.nterms
        for nterm in nterms:
            if nterm == Nonterminal('ε'):
                continue
            X = Elem(nterm)
            rules = g.productions_by_lhs(nterm)
            expr = cls.expr_from_productions(rules)
            eqs.append(RegexEquation.from_expr(expr, X))
        return eqs


def regex_solve(eqs: list[RegexEquation]) -> list[RegexEquation]:
    eqs = eqs.copy()
    size = len(eqs)

    prev_eqs = []
    while prev_eqs != eqs:
        prev_eqs = eqs
        for i in range(size):
            for j in range(size):
                eq = eqs[i]
                subeq = eqs[j]
                if eq.X == subeq.X:
                    continue
                if subeq.beta.has_item(eq.X):
                    res = eq.calculate_result().flatten()
                    # print(f'Подставляем {res} в выражение для {subeq.X}')
                    subeq = subeq.replace_beta(eq.X, res)
                    if subeq.beta.has_item(subeq.X):
                        # print(f'Реорганизовываем выражение для {subeq.X}')
                        subeq = subeq.rearrange_X()
                    eqs[j] = subeq
    return eqs
