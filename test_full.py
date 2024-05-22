from main import FSM, fsm_from_item
from model.rgrammar import RGrammar
from regex_solver import RegexEquation, regex_solve


def test_basic():
    grammar_str = '''
                X1 -> 0 X2 | 1 X1 | ε
                X2 -> 0 X3 | 1 X2
                X3 -> 0 X1 | 1 X3
                '''

    """
    (A|B)*ABB
    """

    grammar = RGrammar.fromstring(grammar_str)
    eqs: list[RegexEquation] = RegexEquation.expr_from_grammar(grammar)
    solved_eqs = regex_solve(eqs)

    interested_regex = list(filter(lambda x: x.X.sym == grammar.start, solved_eqs))[0].calculate_result()

    s = FSM('start', fsm_from_item(interested_regex))

    test_data = [
        ('', True),
        ('0', False),
        ('1', True),
        ('11111', True),
        ('000', True),
        ('1111101111100', True),
        ('111110111110', False),
        ('000', True),
        ('00', False),
        ('0000', False)
    ]

    for text, result in test_data:
        r, _, _ = s.apply(text)
        assert result == r

