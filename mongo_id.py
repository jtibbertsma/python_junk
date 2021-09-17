import re
from functools import singledispatchmethod
from datetime import datetime

class Mongo:
    _match_id = re.compile(r'(?P<timestamp>[a-f0-9]{8})[a-f0-9]{16}').fullmatch

    @singledispatchmethod
    @classmethod
    def is_valid(cls, s):
        """returns True if s is a valid MongoID; otherwise False"""
        return False

    @singledispatchmethod
    @classmethod
    def get_timestamp(cls, s):
        """if s is a MongoID, returns a datetime object for the timestamp; otherwise False"""
        return False

    @is_valid.register(str)
    @classmethod
    def _(cls, s):
        return cls._match_id(s) is not None

    @get_timestamp.register(str)
    @classmethod
    def _(cls, s):
        if (mo := cls._match_id(s)) is not None:
            return cls.hex_to_date(mo.group('timestamp'))
        return False

    @staticmethod
    def hex_to_date(hex):
        return datetime.fromtimestamp(int(hex, 16))