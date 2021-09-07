"""Python class that supports overloaded functions"""

import inspect
import functools

class OverloadedBoundMethod:
    def __init__(self, func, obj):
        self.func = func
        self.obj = obj

    def __repr__(self):
        return f'OverloadedBoundMethod(obj={self.obj}, func={self.func})'

    def __call__(self, *args):
        return self.func(self.obj, *args)

class OverloadedFunc:
    update_wrapper = functools.update_wrapper

    def __init__(self, cls_name):
        self.cls_name = cls_name
        # Map number of args to callables
        self.overload_map = {}

    def __repr__(self):
        return f'OverloadedFunc(overload_map={self.overload_map})'

    def __get__(self, obj, _):
        return OverloadedBoundMethod(self, obj)

    def __call__(self, *args):
        numargs = len(args)
        func = self.overload_map.get(numargs, None)
        if func is None:
            raise AttributeError(f'No version of method "{self.__name__}" in '
                                 f'class "{self.cls_name}" with {numargs - 1} args')
        return func(*args)

    def add_new_overload(self, func):
        if not hasattr(self, '__name__'):
            self.update_wrapper(func)
        self.overload_map[self.compute_arity(func)] = func

    def copy(self):
        cls = type(self)
        func = cls(self.cls_name)
        func.update_wrapper(self)
        func.overload_map = self.overload_map.copy()
        return func

    @staticmethod
    def compute_arity(func):
        """Given a callable, return the number of arguments it takes"""
        return len(inspect.getfullargspec(func).args)

class OverloadDict(dict):
    def __init__(self, cls_name):
        super().__init__()
        self.cls_name = cls_name
        self['__setattr__'] = self._overload_setattr()

    def __repr__(self):
        return f'OverloadDict({super().__repr__()})'

    def __setitem__(self, key, value):
        """Set the dict item, constructing an OverloadedFunc if needed."""
        if (descr := self._get_descr(key, value)):
            descr.add_new_overload(value)
            return super().__setitem__(key, descr)
        return super().__setitem__(key, value)

    def _overload_setattr(self):
        """Build the __setattr__ method for the Overload class"""
        def __setattr__(overload_obj, attr, value):
            """Handle case where a function is written to an instance
            ex:
            >>> obj = Overload()
            >>> Overload.foo = lambda self, x: x
            """
            if (descr := self._get_descr(attr, value)):
                descr = descr.copy()
                descr.add_new_overload(value)
                return object.__setattr__(overload_obj,
                                          attr,
                                          descr.__get__(overload_obj,
                                                        type(overload_obj)))
            return object.__setattr__(overload_obj, attr, value)
        return __setattr__

    def _get_descr(self, key, value):
        """If value is callable, either construct a new empty
        OverloadFunc or return an old OverloadFunc corresponding to key.

        Since this implementation relies on the definition of __setattr__
        on the user class, raise a TypeError if the user class tries to
        overwrite __setattr__. Since __setattr__ is skipped, all methods
        except for __setattr__ are wrapped in OverloadFunc, including
        __init__ and any non-overloaded methods.
        """
        prev = self.get(key, None)
        # The `prev is not None` check here prevents us from raising
        # TypeError when __setattr__ is added in OverloadDict.__init__
        if key == '__setattr__' and prev is not None:
            raise TypeError('Overwriting __setattr__ on class '
                           f'"{self.cls_name}" is forbidden')
        if callable(value):
            if isinstance(prev, OverloadedFunc):
                return prev
            return OverloadedFunc(self.cls_name)
        return None

class Meta(type):
    DICTATTR = '__overload_dict__'

    def __prepare__(name, _):
        return OverloadDict(name)

    def __new__(metacls, name, bases, ns):
        cls = super().__new__(metacls, name, bases, ns)
        # On class creation, python copies ns (the OverloadDict)
        # into a normal dict. Save a reference to the OverloadDict
        # so we can use it in __setattr__
        setattr(cls, metacls.DICTATTR, ns)
        return cls

    def __setattr__(cls, attr, value):
        """Handle case where a function is written to the class
        ex:
        >>> Overload.foo = lambda self, x: x
        """
        if attr == cls.DICTATTR:
            return super().__setattr__(attr, value)
        # Use the OverloadDict logic
        ns = getattr(cls, cls.DICTATTR)
        ns[attr] = value
        return super().__setattr__(attr, ns[attr])

class Overload(metaclass=Meta):
    
    CLS_VAR = 42
    
    def __init__(self):
        self.a = 1
        self.no = 'This is "No parameter" function.'
        self.single = 'This is "Single parameter" function'
        self.two = 'This is "Two parameter" function'
        self.three = 'This is "Three parameter" function'

    def foo(self):
        return self.no

    def foo(self, x):
        return self.single + ':' + str(x)

    def foo(self, x, y):
        return self.two + ':' + str(x) + ',' + str(y)

    def foo(self, x, y, z):
        return self.three + ':' + str(x) + ',' + str(y) + ',' + str(z)
    
    def extra(self):
        return 'This is extra method.'

if __name__ == '__main__':
    obj = Overload()

    print(obj.a)
    print(obj.no)
    print(obj.two)
    print(obj.three)
    print(obj.extra())
    print(obj.CLS_VAR)

    print(obj.foo())
    print(obj.foo(1))
    print(obj.foo(1, 2))
    print(obj.foo(1, 2, 3))

    obj.foo = lambda self, a, b, c, d: 'Hello'

    print(obj.foo())
    print(obj.foo(1,2,3,4))

    def class_foo(self, a, b, c, d):
        return 'Setting attr on class works'

    Overload.foo = class_foo

    print(obj.foo())
    print(obj.foo(1))
    print(obj.foo(1, 2))
    print(obj.foo(1, 2, 3))
    print(obj.foo(1, 2, 3, 4))