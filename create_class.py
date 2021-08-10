from builtins import __build_class__ as build_class

class Dynamic:
    @classmethod
    def __init_subclass__(cls, /, preloaded=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if preloaded is not None:
            for attr, value in preloaded.items():
                setattr(cls, attr, value)
            
def nothing():
    ...

def create_class(class_name, secrets):
    return build_class(nothing,
                       class_name,
                       Dynamic,
                       preloaded=secrets)
