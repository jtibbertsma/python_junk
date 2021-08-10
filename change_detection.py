import re
import operator
from functools import update_wrapper, partial

class _MISSING:
    def __repr__(self):
        return '<MISSING>'
    def __bool__(self):
        return False
MISSING = _MISSING()

def define_proxy_binops(valueattr, modattr):
    def decorator(cls):
        def define_method(name, code, binop):
            globals = {
                'valueattr': valueattr,
                'modattr': modattr,
                'cls': cls,
                'binop': binop,
            }
            locals = {}
            exec('\n'.join(code), globals, locals)
            method = locals[name]
            method.__qualname__ = f'{cls.__qualname__}.{name}'
            setattr(cls, name, method)

        def add_binop(name):
            binop = getattr(operator, name)
            code = [
              f"def {name}(self, other):",
               "    value = getattr(self, valueattr)",
               "    other_value = getattr(other, valueattr) if isinstance(other, cls) else other",
               "    return binop(value, other_value)"]
            define_method(name, code, binop)

        def add_rbinop(rname):
            name = '__' + re.search(r'__r(.+)', rname)[1]
            binop = getattr(operator, name)
            code = [
              f"def {rname}(self, other):",
               "    value = getattr(self, valueattr)",
               "    other_value = getattr(other, valueattr) if isinstance(other, cls) else other",
               "    return binop(other_value, value)"]
            define_method(rname, code, binop)

        def add_ibinop(iname):
            name = '__' + re.search(r'__i(.+)', iname)[1]
            binop = getattr(operator, name)
            code = [
              f"def {iname}(self, other):",
               "    modify = getattr(self, modattr)",
               "    value = getattr(self, valueattr)",
               "    other_value = getattr(other, valueattr) if isinstance(other, cls) else other",
               "    result = binop(value, other_value)",
               "    modify(result)",
               "    return self"]
            define_method(iname, code, binop)

        binops = ['__add__', '__and__', '__concat__', '__contains__', '__eq__',
                  '__floordiv__', '__ge__', '__gt__', '__le__', '__lshift__',
                  '__lt__', '__matmul__', '__mod__', '__mul__', '__ne__', '__or__',
                  '__pow__', '__rshift__', '__sub__', '__truediv__', '__xor__']
        for name in binops:
            add_binop(name)
        rbinops = ['__radd__', '__rsub__', '__rmul__', '__rmatmul__', '__rtruediv__',
                   '__rfloordiv__', '__rmod__', '__rpow__', '__rlshift__',
                   '__rrshift__', '__rand__', '__rxor__', '__ror__']
        for name in rbinops:
            add_rbinop(name)
        ibinops = ['__iadd__', '__iand__', '__iconcat__', '__ifloordiv__', '__ilshift__',
                   '__imatmul__', '__imod__', '__imul__', '__ior__', '__ipow__', '__irshift__',
                   '__isub__', '__itruediv__', '__ixor__']
        for name in ibinops:
            add_ibinop(name)
        return cls
    return decorator

@define_proxy_binops('_value_', '_modify_')
class ProxyAttribute:
    def __init__(self, changeattr, value=MISSING):
        state = '' if value is MISSING else 'INIT'
        object.__setattr__(self, '_changeattr_', changeattr)
        object.__setattr__(self, '_value_', value)
        object.__setattr__(self, '_state_', state)

    def __repr__(self):
        value = self._value_
        state = self._state_
        return f'ProxyAttribute(value={value}, state={state or None})'

    def __getattr__(self, attr):
        if attr == self._changeattr_:
            return self._state_
        return getattr(self._value_, attr)

    def __setattr__(self, attr, value):
        if attr == self._changeattr_:
            raise AttributeError(f"can't set attribute '{self._changeattr_}' on ProxyAttribute")
        return setattr(self._value_, attr, value)

    def __delattr__(self, attr):
        if attr == self._changeattr_:
            raise AttributeError(f"can't delete attribute '{self._changeattr_}' on ProxyAttribute")
        return self._value_.__delattr__(attr)

    def __bool__(self):
        return bool(self._value_)
    
    def __call__(self, *args, **kwargs):
        return self._value_(*args, **kwargs)

    def _modify_(self, new_value):
        if self._value_ != new_value or type(self._value_) != type(new_value):
            new_state = 'MOD' if self._value_ is not MISSING else 'INIT'
            object.__setattr__(self, '_state_', new_state)
            object.__setattr__(self, '_value_', new_value)
        
    def _delete_(self):
        object.__setattr__(self, '_state_', 'DEL')
        object.__setattr__(self, '_value_', MISSING)

def change_detection(cls=None, /, changeattr='get_change'):
    """ Decorator for get_change of class attributes """
    Attribute = partial(ProxyAttribute, changeattr)

    def decorator(cls):
        class Wrapper(cls):
            def __getattribute__(self, attr):
                try:
                    attribute = super().__getattribute__(attr)
                    if not isinstance(attribute, ProxyAttribute):
                        # attribute isn't wrapped yet, initialize it
                        attribute = Attribute(attribute)
                        object.__setattr__(self, attr, attribute)
                    return attribute
                except AttributeError:
                    # non-existent attribute
                    attribute = Attribute()
                    object.__setattr__(self, attr, attribute)
                    return attribute

            def __setattr__(self, attr, value):
                if isinstance(value, ProxyAttribute):
                    value = value._value_
                try:
                    attribute = object.__getattribute__(self, attr)
                    if not isinstance(attribute, ProxyAttribute):
                        # We would get here if the user tries to set an instance attribute
                        # of the same name as a class attribute; attribute is the class
                        # attribute here
                        attribute = Attribute(attribute)
                    attribute._modify_(value)
                    return super().__setattr__(attr, attribute)
                except AttributeError:
                    # Initialize attr
                    attribute = Attribute(value)
                    return super().__setattr__(attr, attribute)

            def __delattr__(self, attr):
                try:
                    attribute = object.__getattribute__(self, attr)
                    attribute._delete_()
                    return None
                except AttributeError:
                    return super().__delattr__(attr)

        update_wrapper(Wrapper, cls, updated=())
        return Wrapper
    
    if cls is None:
        return decorator
    return decorator(cls)