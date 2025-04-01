import re
from typing import Any, TypedDict, Union
from erin.plugins.dice.dice import DiceAction, Dice
from erin.plugins.command.scr.CMDResult import CMDResult


class DiceGamePlayer(TypedDict):
    name: str
    score: int


class TortureGame:
    def __init__(self) -> None:
        self.players: dict[str, DiceGamePlayer] = {}
        self.__sides: int = 100
        self.result = None
        self.max_winners: int = 0
        self.max_losers: int = 0
        self.winners_list = []
        self.losers_list = []
        self.manual_setting = False

    @property
    def sides(self) -> int:
        return self.__sides

    @sides.setter
    def sides(self, sides: int) -> None:
        if Dice.check_sides(sides):
            self.__sides = sides

    def add_player(self, player_id: str, player_name: str) -> None:
        self.players[player_id] = {"name": player_name, "score": 0}
        if self.max_winners == 0 and not self.manual_setting:
            self.max_winners = 1
        elif self.max_losers == 0 and not self.manual_setting and len(self.players) > 1:
            self.max_losers = 1
        elif (
            self.max_winners == 1 and not self.manual_setting and len(self.players) > 10
        ):
            self.max_winners = 2

    def remove_player(self, player_id: str) -> None:
        del self.players[player_id]

    def get_player(self, player_id: str) -> Any:
        return self.players[player_id]

    def get_players_str(self) -> str:
        player_str = "参与玩家: "
        for player in self.players.values():
            player_str += f'\n{player["name"]}'
        return player_str

    def clear(self) -> None:
        self.players = {}

    def play(self) -> None:
        for player in self.players.values():
            player["score"] = DiceAction(f"d{self.sides}").result
        self.result = [
            (player[1]["name"], player[1]["score"], player[0])
            for player in self.players.items()
        ]
        self.result.sort(key=lambda x: x[1], reverse=True)

    def get_result(self) -> tuple[str, list[str]]:
        at_list = []
        result = "本轮结果: \n〰️〰️〰️〰️〰️〰️〰️〰️"
        if not self.result:
            return "还没有进行过游戏，没有结果。", []
        for i, (name, score, id) in enumerate(self.result):
            if i + 1 <= self.max_winners:
                at_list.append(id)
            elif i + 1 > len(self.result) - self.max_losers:
                at_list.append(id)
            result += f"\n{name}：{score}"
        result += "\n〰️〰️〰️〰️〰️〰️〰️〰️\n - "
        return result, at_list

    @classmethod
    def command_handler(
        cls,
        guild_id: str,
        user_id: str,
        user_name: str,
        args: list[str],
        command: Union[str, None] = None,
        at_list: list[dict[str, str | None]] | None = None,
    ) -> CMDResult:
        game_id = guild_id
        game = DiceGame_instances.get(game_id)
        if command == None:
            if not game:
                return CMDResult("游戏尚未开始")
            game.play()
            text, result_at_list = game.get_result()
            return CMDResult(text, result_at_list)
        elif command == "加入":
            if not game:
                return CMDResult("游戏尚未开始")

            game.add_player(user_id, user_name)
            return CMDResult(f"{user_name} 加入了游戏")
        elif command == "离开":
            if not game:
                return CMDResult("游戏尚未开始")
            game.remove_player(user_id)
            return CMDResult(f"{user_name} 离开了游戏")
        elif command == "设置":
            if not game:
                return CMDResult("游戏尚未开始")
            if len(args) == 1:
                if args[0].isdigit():
                    sides = int(args[0])
                    game.sides = sides
                    if game.sides != sides:
                        return CMDResult(
                            "骰子面数错误，应为: [2, 4, 6, 8, 10, 12, 20, 100]"
                        )
                    return CMDResult(f"游戏设置成功，骰子为：{game.sides}")
                else:
                    match = re.search(r"(\d+)(?:v|V)(\d+)", args[0])
                    if match:
                        w = int(match.group(1))
                        l = int(match.group(2))
                        if w + l > len(game.players):
                            return CMDResult("胜利者+失败者不能超过参与人数")
                        game.max_winners = int(match.group(1))
                        game.max_losers = int(match.group(2))
                        game.manual_setting = True
                        return CMDResult(
                            f"游戏设置成功，现在将at {game.max_winners}个胜利者，{game.max_losers}个失败者"
                        )
            return CMDResult("你设置了啥? O.o")
        elif command == "踢出":
            if not game:
                return CMDResult("游戏没有开始")
            if not at_list:
                return CMDResult("请指定要踢出的玩家(At他/她)")
            for at in at_list:
                if at["id"] not in game.players.keys():
                    return CMDResult(f"{at["name"]}都没参加游戏你踢别人干嘛?")
                if not at["id"]:
                    return CMDResult("发生了点问题，联系管理员吧~")
                game.remove_player(at["id"])
            return CMDResult(
                f"{"、".join([player["name"] if player["name"] else "未知名称" for player in at_list])} 被踢出游戏。当前游戏人数: {len(game.players)}"
            )
        elif command == "开始":
            if not game:
                DiceGame_instances[game_id] = cls()
                return CMDResult("游戏开始")
        elif command == "结束":
            if not game:
                return CMDResult("游戏尚未开始")
            del DiceGame_instances[game_id]
            return CMDResult("游戏结束")
        elif command == "查看":
            if not game:
                return CMDResult("游戏尚未开始")
            return CMDResult(game.get_players_str())
        elif command == "重置":
            if not game:
                return CMDResult("游戏尚未开始")
            game.clear()
            return CMDResult("游戏已经重置，需要重新报名。")
        return CMDResult("未知的游戏命令")


DiceGame_instances: dict[str, TortureGame] = {}
