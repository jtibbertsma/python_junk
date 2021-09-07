"""Python class that supports overloaded functions"""

import inspect
import functools

class OverloadedBoundMethod:
    def __init__(self, func, obj):
        self.func = func
        self.obj = obj

    def __call__(self, *args):
        return self.func(self.obj, *args)

class OverloadedFunc:
    update_wrapper = functools.update_wrapper

    @classmethod
    def create(cls, cls_name, func):
        """Create an OverloadedFunc wrapping func"""
        self = cls(cls_name)
        self.add_new_overload(func)
        self.update_wrapper(func)
        return self

    def __init__(self, cls_name):
        self.cls_name = cls_name
        # Map number of args to callables
        self.overload_map = {}

    def __get__(self, obj, _):
        return OverloadedBoundMethod(self, obj)

    def __call__(self, *args):
        numargs = len(args)
        func = self.overload_map.get(numargs, None)
        if func is None:
            raise TypeError(f'No version of method "{self.__qualname__}" in '
                            f'class "{self.cls_name}" with {numargs - 1} args')
        return func(*args)

    def add_new_overload(self, func):
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

    def __setitem__(self, key, value):
        """Set the dict item, constructing an OverloadedFunc if needed."""
        if (descr := self._get_descr(key, value)):
            descr.add_new_overload(value)
            return super().__setitem__(key, descr)
        return super().__setitem__(key, value)

    def _overload_setattr(self):
        """Build the __setattr__ method for the Overload class"""
        def __setattr__(overload_obj, attr, value):
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
        """If value is callable and there is a callable in the dict
        corresponding to key, return the value in the dict wrapped
        with OverloadedFunc. Otherwise, return None.

        Since this implementation relies on the definition of __setattr__
        on the user class, raise a TypeError if the user class tries to
        overwrite __setattr__.
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
            if callable(prev):
                return OverloadedFunc.create(self.cls_name, prev)
        return None

class Meta(type):
    def __prepare__(name, _):
        return OverloadDict(name)

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

    print(obj.foo(1,2,3,4))
