from functools import wraps

class UnexpectedTypeException(TypeError): pass

def expected_type(return_types):
    """Check if decorated function returns object of return_types or raise UnexpectedTypeException.

    Example:

    @expected_type((str,))
    def return_something(input):
        # do stuff here with the input...
        return something

    >>> return_something('The quick brown fox jumps over the lazy dog.')
    'The quick brown fox jumps over the lazy dog.'

    >>> return_something('The quick brown fox jumps over the lazy dog.')
    'Maybe you'll output another string...'

    >>> return_something(None)
    UnexpectedTypeException: Was expecting instance of: str

    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwds):
            result = func(*args, **kwds)
            for T in return_types:
                if isinstance(result, T):
                    break
            else:
                # We didn't break out of the loop
                raise UnexpectedTypeException
            return result

        return wrapper
    return decorator
