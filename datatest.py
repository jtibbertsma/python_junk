from dataclasses import dataclass

@dataclass
class PointData:
    x: int
    y: int
    z: int = 0

class PointNormal:
    def __init__(self, x: int, y: int, z: int = 0):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f'PointNormal(x={self.x},y={self.y},z={self.z})'

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return (self.x, self.y, self.z) == (other.x, other.y, other.x)
        return NotImplemented

    __hash__ = None
