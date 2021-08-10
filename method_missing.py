"""Attempt to replicate ruby's behavior of calling `method_missing` if a method
isn't found
"""
from typing import Any

class MethodMissingObject:
    pass

class MethodMissingDescriptor:
    def __init__(self, parent_object: Any, attr_name: str):
        object.__setattr__(self, '__parent_object__', parent_object)
        object.__setattr__(self, '__attr_name__', attr_name)

    def __setattr__(self, name, value):
        raise AttributeError(f'Can\'t setattr {name}={value} on MethodMissingDescriptor. '
            'Did you mean to call this object?')

    def __getattr__(self, name, value):
        
