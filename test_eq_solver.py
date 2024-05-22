from eq_solver import Op, Expr, Elem


def gen_complicated_eq(op: Op, depth: int = 5, layer_size: int = 10) -> Expr:
    return Expr(
        op,
        list(map(lambda _: gen_complicated_eq(op, depth - 1, layer_size) if depth > 1 else Elem('item'),
                 range(layer_size)))
    )


def test_flatten_sum():
    complicated: Expr = gen_complicated_eq(Op('+'), depth=1)
    assert complicated.depth() == 1
    flatten = complicated.flatten()
    assert flatten.depth() == 1
    assert len(flatten.args) == 10

    complicated: Expr = gen_complicated_eq(Op('+'), depth=3)
    assert complicated.depth() == 3
    flatten = complicated.flatten()
    assert flatten.depth() == 1
    assert len(flatten.args) == 1000

    complicated: Expr = gen_complicated_eq(Op('+'), depth=5)
    assert complicated.depth() == 5
    flatten = complicated.flatten()
    assert flatten.depth() == 1
    assert len(flatten.args) == 100000


def test_flatten_mul_sum():
    eq = Expr(
        Op('*'),
        [
            Expr(
                Op('+'),
                [
                    Elem('a'),
                    Elem('b'),
                ]
            ),
            Expr(
                Op('+'),
                [
                    Elem('c'),
                    Elem('d'),
                ]
            ),
        ]
    )

    assert eq.depth() == 2
    flatten = eq.flatten()
    assert eq.depth() == 2

    target_eq = Expr(
        '+',
        [
            Expr(
                '*',
                ['a', 'c']
            ),
            Expr(
                '*',
                ['b', 'c']
            ),
            Expr(
                '*',
                ['a', 'd']
            ),
            Expr(
                '*',
                ['b', 'd']
            ),
        ]
    )

    assert flatten == target_eq

    assert flatten.flatten() == flatten


def test_replace():
    eq_elems = []
    for i in range(64):
        eq_elems.append(Elem(i))

    eq = Expr(
        '+',
        eq_elems
    )

    assert Elem(42) in eq.args
    assert Elem(-1) not in eq.args

    replaced = eq.replace(Elem(42), Elem(-1))
    assert Elem(42) not in replaced.args
    assert Elem(-1) in replaced.args

    eq = Expr(
        '+',
        [
            '1',
            '34',
            Expr(
                '*',
                ['1', '2']
            )
        ]
    )

    replaced = eq.replace(Expr('*', ['1', '2']), Elem('123'))

    assert replaced.depth() == 1
    assert Elem('123') in replaced.args


def test_extract_simple():
    eq = Expr(
        '+',
        [
            '1', '2', 'X'
        ]
    )
    new_eq, extracted = eq.extract(Elem('X'))
    assert new_eq == Expr(
        '+',
        ['1', '2']
    )
    assert extracted == [
        Elem('X')
    ]


def test_extract_eq():
    eq = Expr(
        '+',
        [
            '1', '2',
            Expr(
                '*',
                [
                    '1', 'X'
                ]
            )
        ]
    )
    ew_eq, extracted = eq.extract(Elem('X'))
    assert ew_eq == Expr(
        '+',
        [
            '1', '2'
        ]
    )

    assert extracted == [
        Expr(
            '*',
            ['1', 'X']
        )]


def test_extract_multiple_eq():
    eq = Expr(
        '+',
        [
            '1',
            Expr('+',
                 [
                   '2',
                   Expr(
                       '*',
                       [
                           '1', 'X'
                       ]
                   )]
                 ),
            Expr(
                '*',
                [
                    'been', 'X'
                ]
            )
        ]
    )
    ew_eq, extracted = eq.extract(Elem('X'))
    assert ew_eq == Expr(
        '+',
        [
            '1', '2'
        ]
    )

    assert extracted == [
        Expr(
            '*',
            ['1', 'X']
        ),
        Expr(
            '*',
            ['been', 'X']
        ),
    ]

    assert isinstance(extracted[0], Expr)
    assert isinstance(extracted[1], Expr)
    extr0 = extracted[0]
    extr1 = extracted[1]

    if isinstance(extr0, Expr) and isinstance(extr1, Expr):  # fake check for a typing system
        assert extr0.extract(Elem('X'))[0] == Expr('*', [Elem('1')])
        assert extr1.extract(Elem('X'))[0] == Expr('*', [Elem('been')])
    else:
        raise RuntimeError('Sun was exploded')
