import time
from typing import TypedDict, Optional
import typing

from forexrateapi.client import Client

from src.data.data import DataManager


class CurrencyRateData(TypedDict):
    timestamp: int
    rates: dict[str, float]


class __Response_data(TypedDict):
    success: Optional[bool]
    timestamp: int
    base: Optional[str]
    rates: dict[str, float]


__api_key = DataManager.get("forexrate_api_key")
__client = Client(__api_key)


def __get_rate() -> __Response_data | None:
    try:
        return __client.fetchLive("CNY")
    except Exception as e:
        return None


def __generate_exchange_rate_data():
    rate_data = __get_rate()
    if rate_data:
        rate_data = typing.cast(dict, rate_data)
        del rate_data["success"]
        del rate_data["base"]
        DataManager.set("currency_rate_data", rate_data)
    rate_data = typing.cast(CurrencyRateData | None, rate_data)
    return rate_data


def get_rate_data() -> dict[str, float] | None:
    rate_data = DataManager.get("currency_rate_data", "null")
    if rate_data == "null":
        rate_data = __generate_exchange_rate_data()
        if not rate_data:
            return

    data_timestamp = rate_data["timestamp"]
    now_timestamp = time.time()
    if now_timestamp - data_timestamp > 864000:
        rate_data = __generate_exchange_rate_data()
    return rate_data["rates"] if rate_data else None
