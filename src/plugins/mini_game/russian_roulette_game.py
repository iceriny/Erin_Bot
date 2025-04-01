import random
from typing import TypedDict, Union

from src.plugins.command.scr.CMDResult import CMDResult
from src.plugins.dice.dice import DiceAction


class RouletteGamePlayer(TypedDict):
    id: str
    name: str
    priority: int
    value: int


class RouletteGame:
    def __init__(self) -> None:
        self.players_list: list[RouletteGamePlayer] = []
        self.current_index: int = 0
        self.__sides: int = 100
        self.current_value: int = 100

    @property
    def sides(self) -> int:
        return self.__sides

    @sides.setter
    def sides(self, sides: int) -> None:
        self.__sides = sides
        self._current_value = sides

    def clear(self) -> None:
        self.players_list: list[RouletteGamePlayer] = []
        self.current_index: int = 0
        self.__sides: int = 100
        self._current_value: int = 100

    def add_player(self, player_id: str, player_name: str) -> None:
        self.players_list.append(
            {
                "id": player_id,
                "name": player_name,
                "priority": len(self.players_list),
                "value": -1,
            }
        )

    def remove_player(self, player_id: str) -> None:
        removed = None
        for i, p in enumerate(self.players_list):
            if p["id"] == player_id:
                removed = i, p
                break
        if removed is not None:
            self.players_list.remove(removed[1])
            if self.current_index > removed[0]:
                self.current_index -= 1

            if self.current_index >= len(self.players_list):
                self.current_index = 0

    def skip_player(self) -> None:
        self.next_round()

    def get_player(self, player_id: str):
        for p in self.players_list:
            if p["id"] == player_id:
                return p

    def get_players_str(self) -> str:
        player_str = ""
        for player in self.players_list:
            player_str += f'\n{player["name"]}'
        return player_str

    def game_end(self):
        priority_list = [i for i in range(len(self.players_list))]
        for player in self.players_list:
            player["priority"] = priority_list.pop(
                random.randint(0, len(priority_list) - 1)
            )
        self.players_list.sort(key=lambda x: x["priority"])
        self.current_index = 0
        self.current_value = self.sides

    def play(self) -> tuple[RouletteGamePlayer | None, bool]:
        if len(self.players_list) == 0:
            return None, False
        current_player = self.players_list[self.current_index]
        current_player["value"] = DiceAction(f"{self.current_value}").result
        self.current_value = current_player["value"]
        if self.current_value == 1:
            self.game_end()
            return current_player, True
        self.next_round()
        return current_player, False

    def next_round(self):
        self.current_index += 1
        if self.current_index >= len(self.players_list):
            self.current_index = 0

    @classmethod
    def command_handler(
        cls,
        guild_id: str,
        user_id: str,
        user_name: str,
        args: list[str],
        command: Union[str, None] = None,
        at_list: list[dict[str, str | None]] | None = None,
    ):
        game_id = guild_id
        game = Roulette_Game_instances.get(game_id)
        if command == None:
            if not game:
                return CMDResult("游戏没有开始")
            if user_id != game.players_list[game.current_index]["id"]:
                return CMDResult("不是你的回合")
            player, result = game.play()
            if not player:
                return CMDResult("游戏中没有参与的玩家，请先加入游戏")
            elif result:
                return CMDResult(
                    f"掷点: {player['value']}! 就是你了!\n新的排名是: \n{game.get_players_str()}",
                    [player["id"]],
                )
            else:
                return CMDResult(
                    f"{player['name']}你的得分是:{game.current_value}，下一位: ",
                    [game.players_list[game.current_index]["id"]],
                )
        elif command == "加入":
            if not game:
                return CMDResult("游戏还未开始，请先开始游戏")
            if game.get_player(user_id):
                return CMDResult("你已经加入了游戏，请勿重复加入")
            game.add_player(user_id, user_name)
            return CMDResult(
                f"{user_name}加入了游戏。当前游戏人数: {len(game.players_list)}"
            )
        elif command == "查看":
            if not game:
                return CMDResult("游戏没有开始")
            return CMDResult(game.get_players_str())
        elif command == "跳过":
            if not game:
                return CMDResult("游戏没有开始")
            game.skip_player()
            return CMDResult(
                f"{user_name}使用命令跳过回合。下一位: ",
                [game.players_list[game.current_index]["id"]],
            )
        elif command == "踢出":
            if not game:
                return CMDResult("游戏没有开始")
            if not at_list:
                return CMDResult("请指定要踢出的玩家(At他/她)")
            for at in at_list:
                if at["id"] not in [player["id"] for player in game.players_list]:
                    return CMDResult(f"{at['name']}都没参加游戏你踢别人干嘛?")
                game.remove_player(at["id"])
            return CMDResult(
                f"{'、'.join([player['name'] if player['name'] else '未知名称' for player in at_list])} 被踢出游戏。当前游戏人数: {len(game.players_list)}"
            )
        elif command == "离开":
            if not game:
                return CMDResult("游戏没有开始")
            if not game.get_player(user_id):
                return CMDResult("你还没有加入游戏")
            game.remove_player(user_id)
            return CMDResult(
                f"{user_name}离开了游戏。当前游戏人数: {len(game.players_list)}"
            )
        elif command == "开始":
            if game:
                return CMDResult("游戏已经开始了")
            Roulette_Game_instances[guild_id] = cls()
            return CMDResult("游戏开始")
        elif command == "设置":
            if not game:
                return CMDResult("游戏没有开始")
            if len(args) == 1 and args[0].isdigit():
                game.sides = int(args[0])
                return CMDResult(f"起始骰子面数设置成功: {game.sides}")

        elif command == "结束":
            if not game:
                return CMDResult("游戏没有开始")
            del Roulette_Game_instances[guild_id]
            return CMDResult("游戏结束")
        elif command == "重置":
            if not game:
                return CMDResult("游戏没有开始")
            Roulette_Game_instances[guild_id].clear()
            return CMDResult("重置成功")
        return CMDResult("未知的游戏命令")


Roulette_Game_instances: dict[str, RouletteGame] = {}
