"""leetcode #91"""
import functools

def num_decodings(encoded: str) -> int:
    if any(c < '0' or c > '9' for c in encoded):
        raise ValueError('bad chars in encoded string')
    # Avoid stack overflow by starting at the end
    for n in reversed(range(0, len(encoded))):
        res = _num_decodings(encoded[n:])
    return res

@functools.lru_cache(maxsize=None)
def _num_decodings(encoded: str) -> int:
    if encoded == '':
        # Base case for `_num_decodings(encoded[2:])` below
        return 1
    if encoded[0] == '0':
        # Invalid string, can't be decoded
        return 0
    if len(encoded) == 1:
        # Base case: Is there only one character left?
        return 1

    if (encoded[0] > '2') or (encoded[0] == '2' and encoded[1] > '6'):
        # No ambiguities found: Both chars must be parsed alone
        return _num_decodings(encoded[1:])
    # Handle ambiguity
    return _num_decodings(encoded[1:]) + _num_decodings(encoded[2:])

# base='1' will print the fibonacci sequence
# base='13' prints the powers of 2
# base='123' prints the powers of 3
def main(base='1'):
    for n in range(1, 101):
        test_case = base * n
        print(f'{n:3}:    {num_decodings(test_case)}')

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) >= 2:
        main(sys.argv[1])
    else:
        main()
