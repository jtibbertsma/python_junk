"""Print a truth table of a sympy logical expression.

Note that sympy has no equivalence logical operator. Xnor has
the same truth table as equivalence, so when printing expressions,
we try to detect a negated Xor and transform its repr to an equivalence
operator.

To construct equivalences, you can use
>>> from sympy.logic.boolalg import Xnor as Equiv

We also transform the Implies repr to use `->` when printing.
"""

from functools import singledispatchmethod
from itertools import chain, product

from sympy import Symbol, S, sympify
from sympy.logic.boolalg import BooleanFunction, Implies, Not, Xor, And, Or

from tabulate import tabulate


__all__ = ['truth_table', 'TruthTable', 'TruthTableBase', 'BoolfuncReprMixin']

DEFAULT_TABLEFMT = 'fancy_grid'

class TruthTableBase:
    # reprs for bools
    TRUE  = 'T'
    FALSE = 'F'

    @classmethod
    def bool(cls, arg) -> str:
        return cls.TRUE if arg else cls.FALSE

    @staticmethod
    def boolfunc_repr(expr: BooleanFunction) -> str:
        return repr(expr)

    def __init__(self, expr: BooleanFunction, *, tablefmt=DEFAULT_TABLEFMT) -> None:
        if isinstance(expr, str):
            expr = sympify(expr)
        if not isinstance(expr, BooleanFunction):
            raise TypeError('TruthTable expects BooleanFunction instances, '
                           f'not `{type(expr)}`')

        self.tablefmt = tablefmt
        self.expressions = sorted(expr.atoms(BooleanFunction),
                                  key=lambda subexpr: len(self.boolfunc_repr(subexpr)))
        self.symbols = sorted(expr.atoms(Symbol), key=repr)

        self.headers = [self.boolfunc_repr(b) for b in chain(self.symbols, self.expressions)]
        self.rows = self.construct_rows()

    def construct_rows(self) -> list[list[str]]:
        rows = []
        for truth_values in self.generate_truth_values():
            model = dict(zip(self.symbols, truth_values))
            row = [self.bool(v) for v in truth_values]

            for expr in self.expressions:
                row.append(self.bool(expr.subs(model)))
            
            rows.append(row)
        return rows

    def generate_truth_values(self):
        return product((S.true, S.false,), repeat=len(self.symbols))

    def __repr__(self):
        return tabulate(self.rows, headers=self.headers, tablefmt=self.tablefmt)

class BoolfuncReprMixin:
    @singledispatchmethod
    @staticmethod
    def boolfunc_repr(expr) -> str:
        return repr(expr)

    @singledispatchmethod
    @classmethod
    def boolfunc_inner_repr(cls, expr) -> str:
        # Wrap repr with parens
        return f'({cls.boolfunc_repr(expr)})'

    @classmethod
    def binary_repr(cls, expr, op):
        return f' {op} '.join(cls.boolfunc_inner_repr(arg) for arg in expr.args)

    @boolfunc_inner_repr.register(Symbol)
    @boolfunc_inner_repr.register(Not)
    @classmethod
    def _(cls, expr):
        return cls.boolfunc_repr(expr)

    @boolfunc_repr.register(Not)
    @classmethod
    def _(cls, expr):
        subexpr = expr.args[0]
        if isinstance(subexpr, Xor):
            # Detected Xnor, print as equivalence operator
            return cls.binary_repr(subexpr, '<->')
        return f'~{cls.boolfunc_inner_repr(subexpr)}'

    @boolfunc_repr.register(And)
    @classmethod
    def _(cls, expr):
        return cls.binary_repr(expr, '&')

    @boolfunc_repr.register(Or)
    @classmethod
    def _(cls, expr):
        return cls.binary_repr(expr, '|')

    @boolfunc_repr.register(Xor)
    @classmethod
    def _(cls, expr):
        return cls.binary_repr(expr, '^')

    @boolfunc_repr.register(Implies)
    @classmethod
    def _(cls, expr):
        return cls.binary_repr(expr, '->')

class TruthTable(BoolfuncReprMixin, TruthTableBase):
    pass

def truth_table(expr, *, tablefmt=DEFAULT_TABLEFMT, table=TruthTable, **kwds) -> None:
    """Prints a truth table for BooleanFunction expr.
    
    The tablefmt arg is passed to the tabulate library when formatting,
    see the tabulate docs for valid values.

    Extra keyword args are passed to the print function.
    """
    print(table(expr, tablefmt=tablefmt), **kwds)
