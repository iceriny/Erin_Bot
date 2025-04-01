from pickledb import PickleDB
from decorator import decorator

import asyncio
import time

from typing import Any


class DataManager:
    __cache = {}
    __db = PickleDB("erin/data/data.db")
    __last_update: float = 0

    @decorator
    @staticmethod
    def __update_last_update(func, *args, **kw):
        result = func(*args, **kw)
        DataManager.__last_update = time.time()
        return result

    async def _data_cache_control(self):
        while True:
            await asyncio.sleep(60)
            if self.__last_update == 0:
                self.__last_update = time.time()
            else:
                if time.time() - self.__last_update > 60:
                    self.__cache.clear()
                    self.__last_update = time.time()

    def __init__(self) -> None:
        asyncio.get_event_loop().create_task(self._data_cache_control())

    @classmethod
    @__update_last_update
    def get(cls, key: str, default: Any | None = None):
        if key in cls.__cache:
            return cls.__cache[key]
        else:
            cls.__db = PickleDB("erin/data/data.db")
            value = cls.__db.get(key)
            if value == False:
                if default is None:
                    raise KeyError(f"Key {key} not found in database.")
                else:
                    return default
            return value

    @classmethod
    @__update_last_update
    def set(cls, key: str, value: Any):
        cls.__cache[key] = value
        cls.__db.set(key, value)

    @classmethod
    @__update_last_update
    def remove(cls, key: str):
        cls.__cache.pop(key, None)
        cls.__db.remove(key)
