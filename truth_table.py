"""Print a truth table of a sympy logical expression"""

from functools import singledispatchmethod
from itertools import chain, product

from sympy import Symbol, S, sympify
from sympy.logic.boolalg import BooleanFunction, Implies

from tabulate import tabulate


__all__ = ['truth_table', 'TruthTable']

def truth_table(expr: BooleanFunction, /, tablefmt='fancy_grid', **kwds) -> None:
    """Prints a truth table for BooleanFunction expr.
    
    The tablefmt arg is passed to the tabulate library when formatting,
    see the tabulate docs for valid values.

    Other keyword args are passed to the print function.
    """
    print(TruthTable(expr, tablefmt=tablefmt), **kwds)

class TruthTable:
    def __init__(self, expr: BooleanFunction, /, tablefmt='fancy_grid') -> None:
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
            row = ['T' if v else 'F' for v in truth_values]

            for expr in self.expressions:
                row.append('T' if expr.subs(model) else 'F')
            
            rows.append(row)
        return rows

    def generate_truth_values(self):
        return product((S.true, S.false,), repeat=len(self.symbols))

    def __repr__(self):
        return tabulate(self.rows, headers=self.headers, tablefmt=self.tablefmt)

    @singledispatchmethod
    @staticmethod
    def boolfunc_repr(expr) -> str:
        return repr(expr)

    @boolfunc_repr.register(Implies)
    @classmethod
    def _(cls, expr):
        return '(' + ' -> '.join(cls.boolfunc_repr(arg) for arg in expr.args) + ')'
