import re
import operator
from dataclasses import dataclass
from collections import defaultdict
from functools import update_wrapper, reduce
from numbers import Number

class Constant(float):
    @classmethod
    def derivative(cls):
        return cls(0)

    def reciprocal(self):
        """Get reciprocal: c.reciprocal() == 1 / c"""
        return Constant(1 / float(self))

    def __repr__(self):
        return f'Constant({float(self)})'

    def __str__(self):
        return f'{self:g}'

    def __add__(self, other):
        if isinstance(other, Term):
            return other + self
        return Constant(float(self) + float(other))

    def __mul__(self, other):
        if isinstance(other, Term):
            return other * self
        return Constant(float(self) * float(other))

@dataclass
class Term:
    coef:  float = 1.0
    power: float = 1.0

    def derivative(self):
        if self.power != 1:
            cls = type(self)
            return cls(self.coef * self.power, self.power - 1)
        return Constant(self.coef)

    def reciprocal(self):
        cls = type(self)
        return cls(1 / self.coef, self.power)

    def __str__(self):
        inner = 'x' if self.power == 1 else f'(^ x {self.power})'
        return inner if self.coef == 1 else f'(* {self.coef} {self.inner})'

    def __add__(self, other):
        if not isinstance(other, Term):
            # Can't add a Constant to a Term
            return NotImplemented
        if self.power != other.power:
            raise ValueError("powers don't match")
        cls = type(self)
        return cls(self.coef + other.coef, self.power)

    def __mul__(self, other):
        if not isinstance(other, (Number, Term)):
            return NotImplemented
        cls = type(self)
        if isinstance(other, Number):
            return cls(float(self.coef * other), self.power)
        return cls(self.coef * other.coef, self.power + other.power)

class operation:
    """Method decorator allowing registration of different behaviors depending
    on the equation's operator. Similar behavior to functools.singledispatchmethod,
    except it works by passing a string to the registration function instead
    of a type. Used for the methods `simplify` and `derivative` on the Equation
    class, which have different behaviors depending on the operator.
    """
    def __init__(self, method):
        update_wrapper(self, method)
        self.registered_methods = defaultdict(lambda: method)

    def register(self, operator):
        def decorator(method):
            self.registered_methods[operator] = method
            return self
        return decorator

    # Allows an operation object to seem like a method
    def __get__(self, obj, cls=None, /):
        method = self.registered_methods[obj.operator]
        return method.__get__(obj, cls)

@dataclass
class Equation:
    operator: str
    terms:    list

    @staticmethod
    def find_closing_paren(index, tokens):
        count = 0
        while index < len(tokens):
            if tokens[index] == '(':
                count += 1
            if tokens[index] == ')':
                count -= 1
                if count == 0:
                    return index
            index += 1
        return None

    @classmethod
    def parsetok(cls, tokens):
        assert len(tokens) >= 4
        assert tokens[0]  == '('
        assert tokens[-1] == ')'

        operator = tokens[1]
        terms = []

        index = 2
        while True:
            token = tokens[index]
            if token == 'x':
                terms.append(Term())
                index += 1
            elif re.match(r'-?\d+(?:\.\d+)?', token) is not None:
                terms.append(Constant(token))
                index += 1
            elif token == '(':
                end_index = cls.find_closing_paren(index, tokens) + 1
                terms.append(cls.parsetok(tokens[index:end_index]))
                index = end_index
            elif token == ')':
                break
            else:
                raise ValueError(f'unknown token {token}')

        equation = cls(operator, terms)
        return equation.simplify()

    @classmethod  
    def parse(cls, s):
        """Return either a Constant, a Term, or an Equation"""
        if re.fullmatch(r'-?\d+(?:\.\d+)?', s) is not None:
            return Constant(s)
        if s == 'x':
            return Term()
        return cls.parsetok(re.findall(r'\(|\)|\w+|-?\d+(?:\.\d+)?|[\^*+/-]', s))

    @operation
    def simplify(self):
        """Simplify the equation, returning a Constant or Term if possible"""
        return self

    def inverted_simplify(self, operator, inverted_operator, get_inverse):
        """Shared implementation of simplify for - and /"""
        inverted_terms = [self.terms[0]] + [get_inverse(term)
                                            if not isinstance(term, Equation)
                                            else term
                                            for term in self.terms[1:]]
        cls = type(self)
        inverted = cls(inverted_operator, inverted_terms).simplify()
        if isinstance(inverted, (Constant, Term)):
            return inverted
        terms      = [inverted.terms[0]] + [get_inverse(term)
                                            if not isinstance(term, Equation)
                                            else term
                                            for term in inverted.terms[1:]]
        if len(terms) == len(self.terms):
            return self
        return cls(operator, terms)

    @simplify.register('+')
    def _(self):
        # Combine Constants 
        constant = Constant(0)
        # Combine Terms with same powers
        term_powers = defaultdict(list)
        newterms = [term for term in self.terms if isinstance(term, Equation)]

        for term in self.terms:
            if isinstance(term, Term):
                term_powers[term.power].append(term)
            elif isinstance(term, Constant):
                constant += term
        
        for power in sorted(term_powers.keys()):
            newterm = reduce(operator.add, term_powers[power], Term(coef=0.0))
            if newterm.coef != 0:
                newterms.append(newterm)
        if constant != 0:
            newterms.append(constant)

        if len(newterms) == len(self.terms):
            return self
        if len(newterms) == 1:
            return newterms[0]
        if len(newterms) == 0:
            return Constant(0)
        cls = type(self)
        return cls('+', newterms)
    
    @simplify.register('-')
    def _(self):
        # Invert terms after the first and apply +
        return self.inverted_simplify('-', '+', lambda term: term * -1)

    @simplify.register('*')
    def _(self):
        # Take the product of everything that isn't an equation
        newterms = [term for term in self.terms if isinstance(term, Equation)]
        non_equation_terms = (term for term in self.terms 
                                   if not isinstance(term, Equation))
        term_product = reduce(operator.mul, non_equation_terms, Constant(1))

        if isinstance(term_product, Term) or term_product != 1:
            newterms.append(term_product)
        if len(newterms) == len(self.terms):
            return self
        if len(newterms) == 1:
            return newterms[0]
        if len(newterms) == 0:
            return Constant(1)
        cls = type(self)
        return cls('*', newterms)
    
    @simplify.register('/')
    def _(self):
        # Invert terms after the first and apply *
        return self.inverted_simplify('/', '*', lambda term: term.reciprocal())

    @operation
    def derivative(self):
        return self

    def __str__(self):
        return f'({self.operator} {" ".join(str(term) for term in self.terms)})'

def diff(s):
    print(s)
    return str(Equation.parse(s).derivative())