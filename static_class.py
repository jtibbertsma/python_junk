"""static_class.py

Defines a class decorator that makes a class "static". ex:

>>> @static_class
>>> class Solution:
...     def f1(arg):
...         return f2(arg + 10)
...     def f2(arg):
...         return arg * 10

>>> Solution().f1(5) == f1(5)
# True

All methods defined in the class are changed to static methods, and
are also available as module level functions. So, if you used static_class
to decorate a Solution class in leetcode, you would be able to define all
functions inside the Solution class without using the self parameter in any
Solution methods.

Doesn't copy __dunder__ class variables.
"""

import sys

__all__ = ['static_class', 'DefinedInModuleError']

class DefinedInModuleError(RuntimeError): pass

def static_class(cls):
    mod_name = cls.__module__
    module = sys.modules[mod_name]
    for k, f in cls.__dict__.items():
        if len(k) < 2 or (k[:2] != '__' and k[-2:] != '__'):
            if hasattr(module, k):
                raise DefinedInModuleError(
                    f'static_class(): object `{k}` of type '
                    f'`{type(getattr(module, k))}` '
                    f'is already defined in module `{mod_name}`')
            if callable(f):
                f = staticmethod(f)
                setattr(cls, k, f)
            if hasattr(f, '__get__'):
                f = f.__get__(object(), object)
            setattr(module, k, f)
    return cls
