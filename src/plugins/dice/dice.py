from typing import Self, Final, Set, Union
import random
import re


class Dice:
    """
    骰子的类
    """

    Optional_Sides: Final[Set[int]] = {2, 4, 6, 8, 10, 12, 20, 100}
    """
    允许的面数常量Set
    """

    def __init__(self, sides):
        self.sides = sides

    def __str__(self) -> str:
        return f"d{self.sides}"

    def roll(self) -> int:
        """
        将骰子投掷一次
        """
        return random.randint(1, self.sides)

    def roll_n(self, n) -> list:
        """
        将骰子投掷n次
        """
        return [self.roll() for _ in range(n)]

    def roll_n_sum(self, n) -> int:
        """
        将骰子投掷n次并求和
        """
        return sum(self.roll_n(n))

    @classmethod
    def check_sides(cls, sides: int) -> bool:
        """
        检查面数是否合法
        """
        return sides in cls.Optional_Sides


class SingleDiceAction:
    """
    单个骰子的动作类
    """

    def __init__(self, n: int, sides: int) -> None:
        # if sides not in Dice.Optional_Sides:
        #     raise ValueError(
        #         "dice must be in the form of NdS (N = number of dice, S = number of sides, S => 2, 4, 6, 8, 10, 12, 20, 100)"
        #     )
        self._dice = Dice(sides)
        self._n = n

    def __add__(self, other: Union[Self, int]) -> int:
        if isinstance(other, int):
            return self.result + other
        return self.result + other.result

    def __sub__(self, other: Union[Self, int]) -> int:
        if isinstance(other, int):
            return self.result - other
        return self.result - other.result

    def __str__(self) -> str:
        return f"{self._n}{self._dice}"

    @property
    def result(self) -> int:
        """
        获取骰子结果
        """
        return self._dice.roll_n_sum(self._n)

    @staticmethod
    def get_sides_and_n(dice: str) -> tuple[int, int]:
        """
        获取骰子的投掷次数和面数
        """
        tokens: list[int] = [int(i) for i in dice.split("d")]

        l = len(tokens)

        # if l == 1 and Dice.check_sides(tokens[0]):
        #     return 1, tokens[0]
        # if l == 2 and Dice.check_sides(tokens[1]):
        #     return tokens[0], tokens[1]
        if l == 1:
            return 1, tokens[0]
        if l == 2:
            return tokens[0], tokens[1]

        raise ValueError(
            "dice must be in the form of NdS (N = number of dice, S = number of sides, S => 2, 4, 6, 8, 10, 12, 20, 100)"
        )


class DiceAction:
    """
    骰子动作类，表示一组投骰子的动作
    """

    _pattern = r"\d+d?\d+|\+|-|\d+"

    def __init__(self, dices: str) -> None:
        self._box: list[tuple[Union[SingleDiceAction, int], str]] = []

        tokens: list[str] = re.findall(self._pattern, dices)
        if len(tokens) == 0:
            raise ValueError("dice cannot be empty")
        elif len(tokens) == 1:
            n, sides = SingleDiceAction.get_sides_and_n(tokens[0])
            self._box.append((SingleDiceAction(n, sides), "+"))
            return

        symbol = "+"
        for token in tokens:
            token = token.strip()

            if token == "+":
                symbol = "+"
                continue
            elif token == "-":
                symbol = "-"
            elif "d" not in token:
                self._box.append((int(token), symbol))
                continue

            n, sides = SingleDiceAction.get_sides_and_n(token)
            self._box.append((SingleDiceAction(n, sides), symbol))

    def __str__(self) -> str:
        result = ""
        for i, (action, symbol) in enumerate(self._box):
            if i == 0 and symbol == "+":
                result += f"{action}"
            else:
                result += f"{symbol}{action}"

        return result

    @property
    def result(self) -> int:
        """
        获取骰子结果, 每次获取都会重新计算结果
        """
        result = 0
        for action, symbol in self._box:
            if isinstance(action, int):
                if symbol == "+":
                    result += action
                elif symbol == "-":
                    result -= action
            elif symbol == "+":
                result += action.result
            elif symbol == "-":
                result -= action.result
        return result
