from math import isqrt
from bisect import bisect_left as lbisect, bisect as rbisect

class Primes:
    calculated_upto = 3
    primelist = [2, 3]
    
    @staticmethod
    def isprime(n):
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for k in range(3, isqrt(n) + 1, 2):
            if n % k == 0:
                return False
        return True

    @classmethod
    def extend_primes(cls, n):
        """Extend the prime list up to n"""
        if cls.calculated_upto >= n:
            return
        start = ((cls.calculated_upto // 2) * 2) + 1
        if cls.primelist[-1] == start:
            start += 2
        cls.calculated_upto = n
        for k in range(start, n + 1, 2):
            if cls.isprime(k):
                cls.primelist.append(k)
                
    def __getitem__(self, index):
        return self.primelist[index]
    
    def __len__(self):
        return len(self.primelist)

def gap(g, m, n):
    primes = Primes()
    primes.extend_primes(n)
    start = lbisect(primes, m)
    end   = rbisect(primes, n)
    
    for k in range(start, end - 1):
        curr, next = primes[k], primes[k + 1]
        if next - curr == g:
            return [curr, next]
    return None
    