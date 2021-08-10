import re
from functools import lru_cache, partial

@lru_cache(maxsize=None)
def construct_k_divisible_dfa(k: int) -> tuple[tuple[int, int], ...]:
    """Construct a DFA (transition table) that accepts the binary
    digits of an integer divisible by k. This DFA has the property that
    if the binary digits for some n lead to DFA state p, then n % k == p
    """
    dfa = []
    for n in range(k):
        zero_transition = (n * 2) % k
        one_transition = ((n * 2) + 1) % k
        dfa.append((zero_transition, one_transition))
    return tuple(dfa)

def dfa_modulo(dfa, n: int) -> int:
    """Use the dfa to evaluate n % k (k == len(dfa))"""
    current_state = 0
    for binary_digit in bin(n)[2:]:
        current_state = dfa[current_state][int(binary_digit)]
    return current_state

def dfa_divisible(dfa, n: int) -> bool:
    """Use the dfa to determine whether n is divisible b k (k == len(dfa))"""
    return dfa_modulo(dfa, n) == 0

def modulo(n: int, k: int) -> int:
    """n % k"""
    return dfa_modulo(construct_k_divisible_dfa(k), n)

def divisible(n: int, k: int) -> bool:
    """n % k == 0"""
    return dfa_divisible(construct_k_divisible_dfa(k), n)

divisible_by_7 = partial(dfa_divisible, construct_k_divisible_dfa(7))

def _first_no_star(s):
    i = 1
    while i < len(s) and s[i] == '*':
        i += 2
    return i - 1

def _simplify(s):
    if '(' in s:
        return s
    if '|' in s:
        lhs, rhs = s.split('|')
        lhs = _simplify(lhs)
        rhs = _simplify(rhs)
        if rhs.startswith(lhs):
            return rhs
        i = _first_no_star(rhs)
        if rhs[i:].startswith(lhs):
            return rhs
        return lhs + '|' + rhs
    if len(s) < 4:
        return s
    if s[1] == '*':
        if s[3] == '*' and s[0] == s[2]:
            return _simplify(s[2:])
        return s
    return s[0] + _simplify(s[1:])

def _wrap(s, star=False):
    if s == '':
        return ''
    s = _simplify(s)
    if len(s) == 2 and s[1] == '*' and star is True:
        return s
    if len(s) == 1 and star is True:
        return s + '*'
    if '|' in s or star is True:
        return f"(?:{s}){'*' if star else ''}"
    return s

def kleen_algorithm(DFA_Transition_Table) -> str:
    """Use kleen's algorithm to construct a regular expression
    from the DFA transition table. This implementation makes some
    assumptions about the structure of the DFA that are true of
    any DFA constructed by the 'construct_k_divisible_dfa' function:
      - The alphabet is ('0', '1')
      - There is one accept state, state 0
      - The digit '0' from the accept state points back to the accept state
      - The digit '1' from the highest state (the kth state) points to
        the highest state
      - No states other than the first and last point to themselves
    """
    highest_state = len(DFA_Transition_Table) - 1

    @lru_cache(maxsize=None)
    def r(p: int, q: int, k: int) -> str:
        if k >= 0:
            # The recursive formula is:
            # r(p, q, k) = r(p, q, k-1) | r(p, k, k-1) r(k, k, k-1)* r(k, q, k-1)
            # Google 'kleen's algorithm' for info on where this comes from
            w = r(p, q, k-1)
            x = r(p, k, k-1)
            y = r(k, k, k-1)
            z = r(k, q, k-1)
            lhs = w
            rhs = ''
            if x and z:
                rhs = _wrap(x) + _wrap(y, star=True) + _wrap(z)
            if lhs and rhs:
                return _wrap(lhs) + '|' + _wrap(rhs)
            return lhs or rhs
        # k is -1. The meaning of r(p, q, -1) is a regular expression that gets
        # us from p to q without going through any intermediate states. To
        # construct the expression we make the assumptions about the structure
        # of the DFA that are listed above
        if p == 0 and q == 0:
            return '0*'
        if p == highest_state and q == highest_state:
            return '1*'
        p_state = DFA_Transition_Table[p]
        if p_state[0] == q:
            return '0'
        if p_state[1] == q:
            return '1'
        return ''

    return r'(?=\d)' + _wrap(r(0, 0, highest_state)) + '$'
