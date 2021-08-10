from itertools import count, islice
from functools import singledispatchmethod
from math import sqrt

class PrimeMeta(type):
    """Make the Primes class subscriptable"""
    @singledispatchmethod
    def __getitem__(cls, slice):
        return cls.get_slice(slice.start, slice.stop, slice.step)

    @__getitem__.register(int)
    def _(cls, k):
        return cls.get(k)

class Primes(metaclass=PrimeMeta):
    """Calculate and cache primes using a progressive sieve"""
    primelist = []
    primary_stream = None

    def __init__(self, *args, **kwargs):
        raise TypeError("Don't instantiate Primes; use classmethods instead")

    @classmethod
    def sieve(cls):
        """Iterate through every prime number"""
        yield from (2, 3, 5, 7)
        mark_to_step = {}      # mapping from position in sieve (k) to a prime
        subsieve = cls.sieve() # primes from the recursive sieve are used
        next(subsieve)         # to mark composites in the current sieve
        sieve_factor = next(subsieve)
        prime_squared = sieve_factor * sieve_factor # == 9
        for k in count(prime_squared, 2):  # every odd number starting at 9
            if k in mark_to_step:
                # Mark the next composite of this prime
                step = mark_to_step.pop(k)
            elif k < prime_squared:
                # k wasn't marked by the sieve, so it's prime
                yield k
                continue
            else:
                # k == prime_squared
                # Add the next prime (sqrt k) to the sieve and mark
                # its next multiple that hasn't been found yet
                step = 2 * sieve_factor
                sieve_factor = next(subsieve)
                prime_squared = sieve_factor * sieve_factor
            k += step
            while k in mark_to_step:
                k += step
            mark_to_step[k] = step
    stream = sieve

    @classmethod
    def extend_primes(cls, k):
        """Extend the primelist up to kth prime number"""
        if len(cls.primelist) >= k:
            return
        if cls.primary_stream is None:
            cls.primary_stream = cls.sieve()
        for _ in range(k - len(cls.primelist)):
            cls.primelist.append(next(cls.primary_stream))

    @classmethod
    def isprime(cls, n):
        """Check if a number is prime by iterating through a new sieve"""
        sqrt_n = isqrt(n) + 1
        for p in cls.sieve():
            if n % p == 0:
                return False
            if p > sqrt_n:
                return True

    @classmethod
    def get(cls, k):
        """Get the kth prime number (1 indexed)"""
        if k <= 0:
            raise IndexError('Fetching the 0th or -nth prime is forbidden')
        cls.extend_primes(k)
        return cls.primelist[k - 1]

    @classmethod
    def get_slice(cls, start, stop, step):
        if any(arg is not None and arg < 0 for arg in (start, stop, step)):
            raise IndexError('Negative arguments in slices are forbidden')
        if stop is None:
            raise IndexError('Infinite slices are forbidden')
        cls.extend_primes(stop)
        return islice(cls.primelist, start, stop, step)

    @classmethod
    def clear(cls):
        """Delete all cached primes"""
        cls.primary_stream = None
        cls.primelist.clear()

################# Solution #################
