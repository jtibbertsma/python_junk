"""Create a line of node code that defines variable `palindromeMatcher`, which
is a regex that matches palindromes in a string. For example,
'I Like Naan'.match(palindromeMatcher) would match 'Naan'.
"""

def p(k):
    print(regex(k))

def regex(k: int) -> str:
    """Argument `k` is the number of groups to attempt to match.
    Node doesn't have recursive regular expressions, so the only way is
    to spam capturing groups and back references.
    """
    return f'const palindromeMatcher = /{"|".join(generate_regex_parts(k))}/ig;'

def generate_regex_parts(k: int):
    """Yield regex parts for palidromes length 3 to k*2 + 1. Each length
    has its own pattern that can be used as alternatives in the main pattern.
    """
    # Match a word consisting of a single character
    yield r"\b\w\b"

    s = 0   # backreference ids generated so far
    for n in range(1, k + 1):
        yield regex_part(n, s)
        s += n

def regex_part(n: int, s: int) -> str:
    """Return a pattern matching a palidrome of length n*2 or n*2 + 1. This is
    accomplished by constructing a pattern with n capture groups and n
    corresponding backreferences.

    However, the backreferences have to be numbered assuming that `regex_part`s
    have already been generated for 1...n-1 for the same expression, so the
    cumulative sum of backreferences seen so far is passed as argument `s`.
    """
    front  = r"(\w)" * n
    middle = r"\w?"
    back   = ''.join('\\' + str(x) for x in range(s + n, s, -1))

    return r"\b" + front + middle + back + r"\b"