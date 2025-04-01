import re
from src.plugins.command.scr.calculator.forexrate_api import get_rate_data


class CurrencyParse:
    __currency_code_dict = None

    @classmethod
    def currency_code_dict(cls):
        if not cls.__currency_code_dict:
            with open("erin/data/currency.dict", "r", encoding="utf-8") as f:
                cls.__currency_code_dict = eval(f.read())
        return cls.__currency_code_dict

    @classmethod
    def get_currency_code(cls, currency_name: str) -> str | None:
        code = cls.currency_code_dict().get(currency_name)
        if code is None:
            for item in cls.currency_code_dict().values():
                if currency_name.upper() == item["code"]:
                    return item["code"]
                if currency_name in item["area"]:
                    if item["code"] == "":
                        return
                    return item["code"]
        else:
            return code["code"]

    def __init__(self, original_text: str):
        self.original_text = original_text
        self.original_code = None
        self.currency_code = None
        self.price = None
        self.rate = None
        self.parse()

    @property
    def done(self) -> bool:
        return (
            self.original_code != None
            and self.currency_code != None
            and self.price != None
        )

    def parse(self):

        divided_list = self.original_text.split(r">")
        if len(divided_list) != 2:
            return
        left_text, right_text = divided_list

        match = re.match(r"(\d+\.?\d*)\s?(.+)", left_text, re.I)
        if not match:
            return
        price, original_cur = match.groups()
        currency_cur = right_text
        self.price = float(price)
        self.original_code = self.get_currency_code(original_cur.strip())
        self.currency_code = self.get_currency_code(currency_cur.strip())

    def convert(self):
        if (
            self.original_code is None
            or self.currency_code is None
            or self.price is None
        ):
            raise ValueError("参数错误")
        rate_data = get_rate_data()
        if not rate_data:
            return "获取汇率失败，请稍后重试"
        CHY_to_original_rate = rate_data.get(self.original_code)
        CHY_to_currency_rate = rate_data.get(self.currency_code)
        if not CHY_to_original_rate:
            return f"不支持该币种的转换: {self.original_code}"
        if not CHY_to_currency_rate:
            return f"不支持该币种的转换: {self.currency_code}"
        self.rate = CHY_to_currency_rate / CHY_to_original_rate
        # CHY_price = self.price / CHY_to_original_rate
        target_price = self.price * self.rate
        return f"{self.price}({self.original_code}) ≈ {target_price:.4f}({self.currency_code}) [汇率≈{self.rate:.4f}]"


class CurrencyCal:
    def __init__(self, currency_expression: str) -> None:
        self.currency_parse = CurrencyParse(currency_expression)
        self._result = ""
        if not self.currency_parse.done:
            self._result = f"表达式解析失败，请检查换算表达式。\n解析结果: {self.currency_parse.original_code}>{self.currency_parse.currency_code}:{self.currency_parse.price}"
        else:
            self.calculate()

    def __str__(self) -> str:
        return self._result

    def calculate(self):
        # TODO: 添加货币计算逻辑
        self._result = self.currency_parse.convert()
