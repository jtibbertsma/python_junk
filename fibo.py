from dataclasses import dataclass
from typing import ClassVar
from functools import reduce
from operator import matmul

@dataclass
class FiboMatrix:
    """
    Given that:

        [1, 1] ** n  ==  [fib(n+1), fib(n)  ]
        [1, 0]           [fib(n),   fib(n-1)]

    we can use the rule x**(n + m) == x**n * x**m to compute
    the nth fibonacci in O(log n) time.

    The strategy here is represent n as a sum of powers of 2,
    and find matrices corresponding to each power of two. The
    nth matrix is then the product of each power of two matrix.
    """
    r1c1: int
    r1c2: int
    r2c1: int
    r2c2: int

    _pow2_cache_pos: ClassVar[dict] = {} # Maps powers of 2 to matrices
    _pow2_cache_neg: ClassVar[dict] = {} # Same but for the inverse matrix

    @classmethod
    def compute_fib(cls, n):
        """
        Compute the nth fibonacci number
        """
        if n == 0:
            return 0

        if not cls._pow2_cache_pos:
            cls._pow2_cache_pos[1] = cls(1, 1, 1,  0)
            cls._pow2_cache_neg[1] = cls(0, 1, 1, -1) # inverse of 1, 1, 1, 0

        if n < 0:
            cache = cls._pow2_cache_neg
            m = cls.getfibmatrix(cache, -n)
            return m.r1c2

        cache = cls._pow2_cache_pos
        m = cls.getfibmatrix(cache, n)
        return m.r1c2

    @classmethod
    def getfibmatrix(cls, cache, n):
        p = cls.next_lowest_pow2(n)
        if p not in cache:
            cls.fill_pow2_cache(cache, p)

        pow2_matrices = []
        while p > 0:
            if p & n:
                pow2_matrices.append(cache[p])
            p >>= 1

        return reduce(matmul, pow2_matrices)

    @staticmethod
    def next_lowest_pow2(n):
        p = 1
        while p <= n:
            p <<= 1
        return p >> 1

    @staticmethod
    def fill_pow2_cache(cache, p):
        n = next(reversed(cache.keys()))
        while n < p:
            m = cache[n]
            n = n * 2
            cache[n] = m @ m

    def __matmul__(self, other):
        r1c2 = self.r1c1 * other.r1c2 + self.r1c2 * other.r2c2
        r2c1 = r1c2 # Always equal for fibonacci matrices
        r2c2 = self.r2c1 * other.r1c2 + self.r2c2 * other.r2c2
        r1c1 = r1c2 + r2c2

        cls = type(self)
        return cls(r1c1, r1c2, r2c1, r2c2)

fibo = FiboMatrix.compute_fib