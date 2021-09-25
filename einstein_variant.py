"""Word problem based on the classic Eistein logic puzzle, from
video game `Dishonored 2`.

The Jindosh Problem

At the dinner party were Lady Winslow, Doctor Marcolla, Countess Contee,
Madam Natsiou, and Baroness Finch.

The women sat in a row. They all wore different colors and [character] wore
a jaunty [color] hat. [Character] was at the far left, next to the guest
wearing a [color] jacket. The lady in [color] sat left of someone in [color].
I remember that [color] outfit because the woman spilled her [drink] all over it.
The traveler from [city] was dressed entirely in [color]. When one of the dinner
guests bragged about her [heirloom], the woman next to her said they were finer in
[city], where she lived.

So [character] showed off a prized [heirloom], at which the lady from [city]
scoffed, saying it was no match for her [heirloom]. Someone else carried a
valuable [heirloom] and when she saw it, the visitor from [city] next to her
almost spilled her neighbor's [drink]. [Character] raised her [drink] in
toast. The lady from [city], full of [drink], jumped up onto the table falling
onto the guest in the center seat, spilling the poor woman's [drink]. Then
[character] captivated them all with a story about her wild youth in [city].

In the morning there were four heirlooms under the table: [heirloom],
[heirloom], [heirloom], and [heirloom].

But who owned each? 
"""
from enum import Enum, auto
from dataclasses import dataclass

class Character(Enum):
    Winslow = auto()
    Marcolla = auto()
    Contee = auto()
    Natsiou = auto()
    Finch = auto()

class Color(Enum):
    Blue = auto()
    Green = auto()
    Red = auto()
    White = auto()
    Purple = auto()

class Drink(Enum):
    Wine = auto()
    Whisky = auto()
    Beer = auto()
    Absinthe = auto()
    Rum = auto()

class City(Enum):
    Karnaca = auto()
    Dunwall = auto()
    Fraeport = auto()
    Baleton = auto()
    Dabohkva = auto()

class Heirloom(Enum):
    Diamond = auto()
    Tin = auto()
    Medal = auto()
    Pendant = auto()
    Ring = auto()

@dataclass
class Position:
    place: int
    character: Character = None
    color: Color = None
    drink: Drink = None
    city: City = None
    heirloom: Heirloom = None

class Table(list):
    def __init__(self):
        super().__init__((Position(place=n + 1) for n in range(5)))
