from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Union


class Item:

    def replace(self, replace_what: Item, replace_with: Item) -> Item:
        if self == replace_what:
            return replace_with
        return self

    def depth(self) -> int:
        return 0

    def has_item(self, what: Item) -> bool:
        return self == what


@dataclass(frozen=True)
class Elem(Item):
    sym: Any

    def __repr__(self) -> str:
        return str(self.sym)

    def __eq__(self, other):
        return isinstance(other, Elem) and self.sym == other.sym


@dataclass
class Closure(Item):
    child: Item

    def __init__(self, child: Item):
        while isinstance(child, Closure):
            # Сразу раскрываем замыкание, поскольку (a*)* => a*
            child = child.child
        while isinstance(child, Expr) and len(child.args) == 1:
            child = child.args[0]
        self.child = child

    def __repr__(self):
        if isinstance(self.child, Expr):
            if len(self.child.args) > 0:
                return f'(({self.child})*)'
            elif len(self.child.args) == 1:
                return f'({self.child.args[0]}*)'
        return f'{self.child}*'

    def replace(self, replace_what: Item, replace_with: Item) -> Item:
        if self.child == replace_what:
            return Closure(replace_with)
        return self

    def __eq__(self, other):
        return isinstance(other, Closure) and self.child == other.child


@dataclass(frozen=True)
class Op:
    sym: Any

    def __repr__(self) -> str:
        if self.sym == '*':
            return '×'
        return str(self.sym)


@dataclass
class Expr(Item):
    op: Op
    args: list[Item]

    def __init__(self, op: Union[Op, str], args: list[Any]):
        if isinstance(op, str):
            op = Op(op)
        real_args = []
        for arg in args:
            if not issubclass(type(arg), Item):
                arg = Elem(arg)
            real_args.append(arg)

        if op.sym == '+':
            uniq_args = []
            for arg in real_args:
                if isinstance(arg, Expr):
                    uniq_args.append(arg)
                elif arg not in uniq_args:
                    uniq_args.append(arg)
            real_args = uniq_args

        self.op = op
        self.args = real_args

    def has_item(self, what: Item) -> bool:
        for arg in self.args:
            if arg.has_item(what):
                return True
        return False

    def extract(self, what: Item) -> tuple[Expr, list[Item]]:
        filtered_args = []
        extracted_args = []
        for arg in self.flatten().args:
            if isinstance(arg, Expr):
                new_eq, extracted = arg.extract(what)
                if len(extracted):
                    extracted_args.append(arg)
                else:
                    filtered_args.append(arg)
            else:
                if arg != what:
                    filtered_args.append(arg)
                else:
                    extracted_args.append(arg)

        return Expr(self.op, filtered_args).flatten(), extracted_args

    def depth(self) -> int:
        max_depth = 0
        for arg in self.args:
            max_depth = max(max_depth, arg.depth() + 1)
        return max_depth

    def replace(self, replace_what: Item, replace_with: Item) -> Expr:
        new_args = []
        for arg in self.args:
            arg = arg.replace(replace_what, replace_with)
            if arg == replace_what:
                arg = replace_with
            new_args.append(arg)
        return Expr(self.op, new_args)

    def unfold_singles(self) -> Expr:
        new_args = []
        args = self.args
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, Expr):
                return arg.unfold_singles()
        for arg in args:
            if isinstance(arg, Expr):
                if len(arg.args) == 0:
                    continue
                elif len(arg.args) == 1:
                    new_args.append(arg.args[0])
                else:
                    new_args.append(arg.unfold_singles())
            elif isinstance(arg, Closure):
                child = arg.child
                if isinstance(child, Expr):
                    child = child.unfold_singles()
                new_args.append(Closure(child))
            else:
                new_args.append(arg)
        return Expr(self.op, new_args).flatten()

    def flatten(self) -> Expr:
        new_args = []
        for arg in self.args:
            if isinstance(arg, Expr):
                arg = arg.flatten().unfold_singles()
                if arg.op == self.op:
                    new_args += arg.args
                else:
                    new_args.append(arg)
            else:
                new_args.append(arg)

        if self.op.sym == '*' and any(map(lambda a: isinstance(a, Expr) and a.op.sym == '+', new_args)):
            args = new_args
            new_args = []
            sums: list[Expr] = []
            for arg in args:
                if isinstance(arg, Expr) and arg.op.sym == '+':
                    sums.append(arg)
                else:
                    new_args.append(arg)
            if len(new_args) > 0:
                for arg in new_args:
                    sums.append(
                        Expr(
                            Op('+'),
                            [arg]
                        )
                    )

            new_sums = []
            while len(sums) > 1:
                inserting_sum = sums[-1]
                sums = sums[:-1]

                for arg in inserting_sum.args:

                    for s in sums:
                        sum_els = []
                        for x in s.args:
                            sum_els.append(Expr(Op('*'), [arg, x]))
                        new_sums.append(
                            Expr(
                                Op('+'),
                                sum_els
                            )
                        )
            return Expr(Op('+'), new_sums).flatten()

        return Expr(self.op, new_args)

    def __repr__(self) -> str:
        return f' {self.op} '.join(map(lambda x:
                                       f'({x})' if isinstance(x, Expr) else
                                       str(x), self.args))

    def __eq__(self, other) -> bool:
        if not isinstance(other, Expr):
            return False
        if len(self.args) != len(other.args):
            return False
        for arg in self.args:
            if arg not in other.args:
                return False
        return True
