import random
from typing import Literal, Self, Union, Callable, TypedDict, Any, cast
from src.plugins.command.scr.CMDResult import CMDResult


class Profession(TypedDict):
    desc: str
    skill: Callable[["Bomb_disposal_player", "BombDisposalGame", str | None], str]


class Bomb_disposal_player:

    def __init__(self, name: str, id: str, priority: int) -> None:
        self.__name = name
        self.id = id
        self.width = 0
        self.priority = priority
        self.triggered_event: str = "\n没什么有趣的事情发生..."
        # TODO: 职业系统
        self.profession: str | None = None
        self.skill_activated: bool = False
        self.skill_freeze: bool = False

    @property
    def name(self) -> str:
        if self.profession:
            return f"「 {self.profession} 」{self.__name}"
        return self.__name

    def __skill_for_None(self, _game: "BombDisposalGame", _arg: str | None = None):
        return f"{self.name} ⚠️ 玩家没有技能，无法使用技能。"

    def __skill_for_violent(self, _game: "BombDisposalGame", _arg: str | None = None):
        return f"{self.name} ✅ 技能激活，现在{self.__name}在下一次拆弹可以拆掉最大100长度的引线了。"

    def __skill_for_quality_inspector(
        self, game: "BombDisposalGame", _arg: str | None = None
    ):
        max_fuse = game.max_fuse
        distance = max_fuse - game.fuse_limit[0]
        quality = distance / (game.fuse_limit[1] - game.fuse_limit[0])
        quality_desc = ""
        if quality < 0.2:
            quality_desc = "劣质的"
        elif quality < 0.4:
            quality_desc = "稍差的"
        elif quality < 0.6:
            quality_desc = "普通的"
        elif quality < 0.8:
            quality_desc = "优质的"
        elif quality < 1:
            quality_desc = "完美的"
        return f"{self.name} ✅ 发动了技能，你们面前的炸弹，算是个{quality_desc}炸弹。"

    def __skill_for_observer(
        self, game: "BombDisposalGame", _arg: str | None = None
    ) -> str:
        fuse = game.fuse
        schedule = fuse / game.max_fuse
        schedule_desc = ""
        if schedule < 0.2:
            schedule_desc = "马上爆炸了!"
        elif schedule < 0.4:
            schedule_desc = "引信所剩不多了。"
        elif schedule < 0.6:
            schedule_desc = "还算安全。"
        elif schedule < 0.8:
            schedule_desc = "非常安全。"
        elif schedule < 1:
            schedule_desc = "才刚刚开始呢!"
        return f"{self.name} ✅ 发动了技能，你们面前的炸弹{schedule_desc}"

    def __skill_for_reloader(self, game: "BombDisposalGame", _arg: str | None = None):
        game.fuse += int(game.max_fuse * 0.2)
        return f"{self.name} ✅ 发动了技能，别人拆弹你装弹? 引信长度增加了20%(相对于初始引信的长度)。"

    def __skill_for_stabler(
        self, game: "BombDisposalGame", _arg: str | None = None
    ) -> str:
        game.stable = True
        return f"{self.name} ✅ 发动了技能，炸弹保持稳固状态一回合。"

    def __skill_for_commander(self, game: "BombDisposalGame", _arg: str | None) -> str:
        if _arg is None:
            return f"{self.name} ⚠️ 发动技能但没有指定数值。"
        correction_value = 0
        try:
            correction_value = max(1, min(int(_arg), 10))
            game.correction_value = correction_value
        except ValueError:
            return f"{self.name} ⚠️ 发动技能时指定的数值有误。"
        return f"{self.name} ✅ 发动了技能，下回合的玩家将听从指挥将数值增加或减少对应的值。"

    professions: dict[str | None, Profession] = {
        None: {"desc": "平民", "skill": __skill_for_None},
        "暴力拆弹专家": {
            "desc": "暴力拆弹专家，可将下次最大拆除引信调整为100。",
            "skill": __skill_for_violent,
        },
        "质检官": {
            "desc": "质检员，可查看炸弹引信粗略的最大长度。",
            "skill": __skill_for_quality_inspector,
        },
        "观察员": {
            "desc": "观察员，可查看炸弹引信的模糊的剩余长度。",
            "skill": __skill_for_observer,
        },
        "装弹专家": {
            "desc": "装弹专家，别人拆弹你装弹? 可以发动技能将当前引信长度增加20%(相对于初始引信的长度)。",
            "skill": __skill_for_reloader,
        },
        "稳态者": {
            "desc": "稳态者,发动技能后，下回合如果炸弹爆炸，将稳固炸弹结构，强制延迟。可以在发动技能将归零的引信在0的基础上强制增加1~10。",
            "skill": __skill_for_stabler,
        },
        "指挥官": {
            "desc": "指挥官，可以指定下回合的玩家的输入数值 加或减 1~10。",
            "skill": __skill_for_commander,
        },
    }

    def activate_skill(self, game: "BombDisposalGame", arg: str | None = None) -> str:
        if not self.profession:
            return "⚠️ 玩家没有职业，无法使用技能。"
        else:
            self.skill_activated = True
            self.skill_freeze = True
            profession = self.professions.get(self.profession)
            if profession:
                skill = profession["skill"]
                return skill(self, game, arg)
            else:
                return f"{self.name} ⚠️ 玩家没有技能，无法使用技能。"

    def __repr__(self) -> str:
        return f"< VV Bomb_disposal_player VV >\n**name:{self.__name} id:{self.id} priority:{self.priority} triggered_event:{self.triggered_event}**"


class BombDisposalGame:
    def __init__(self) -> None:
        self.players_list: list[Bomb_disposal_player] = []
        self.__current_index: int = 0
        self.fuse_limit: tuple[int, int] = (80, 120)
        self.init_fuse()

        self.stable = False
        self.correction_value = 0

    def __repr__(self) -> str:
        return f"< VV BombDisposalGame VV >\n**players_list:list({len(self.players_list)}) current_index:{self.current_index} fuse_limit:{self.fuse_limit} fuse:{self.fuse}**"

    @property
    def current_index(self) -> int:
        if self.__current_index >= len(self.players_list):
            self.__current_index = len(self.players_list) - 1
        return self.__current_index

    @current_index.setter
    def current_index(self, index: int) -> None:
        self.__current_index = index % len(self.players_list)

    def init_fuse(self) -> None:
        a, b = self.fuse_limit
        self.fuse = random.randint(a, b)
        self.max_fuse = self.fuse

    def set_fuse_limit(self, a: int, b: int) -> None:
        self.fuse_limit = (a, b)
        self.init_fuse()

    def clear(self) -> None:
        self.players_list: list[Bomb_disposal_player] = []
        self.__current_index: int = 0

    def add_player(self, player_id: str, player_name: str) -> None:
        if player_id in [p.id for p in self.players_list]:
            return
        self.players_list.append(
            Bomb_disposal_player(player_name, player_id, len(self.players_list))
        )

    def remove_player(self, player_id: str) -> None:
        removed = None
        for i, p in enumerate(self.players_list):
            if p.id == player_id:
                removed = i, p
                break
        if removed is not None:
            self.players_list.remove(removed[1])
            if self.current_index > removed[0]:
                self.current_index -= 1

    def skip_player(self) -> None:
        self.current_index += 1

    def get_player(self, player_id: str):
        for p in self.players_list:
            if p.id == player_id:
                return p

    def get_current_player(self) -> Bomb_disposal_player | None:
        if len(self.players_list) == 0:
            return None
        return self.players_list[self.current_index]

    def get_random_players(self, n: int):
        if n > len(self.players_list):
            return self.players_list
        random_players = random.sample(self.players_list, n)
        return random_players

    def get_players_str(self) -> str:
        player_str = ""
        for player in self.players_list:
            player_str += f"\n{player.name}"
        return player_str

    Events_desc = {
        "random": "{name}轻轻的手抖了下，与他想要达成的效果有些许的不一样。({name}的数值有±5点的误差)",
        "skip": "{name}非常完美的处理了炸弹引信，几乎没有燃烧一点! ({name}跳过该回合)",
        "boom": "{name}直接触碰了核心机关，这会发生....BOOOOM!!!~ ({name}直接导致炸弹爆炸了。)",
        "intense": "{name}不小心触碰到了什么机关，炸弹引信飞速的燃烧了很多! ({name}实际产生的数值扩大了2倍)",
        "halved": "{name}小心翼翼的...也太小心了叭?! (实际产生的数值是{name}想要的二分之一)",
        "big random": "{name}专注的处理着炸弹，但...一个没站好，差点摔倒了，当然就没看到自己到底按到了什么。({name}的数值产生了大量的误差)",
    }

    def play(
        self, width: int
    ) -> tuple[None, Literal[False]] | tuple[Bomb_disposal_player, bool]:
        if len(self.players_list) == 0:
            return None, False

        current_player = self.players_list[self.current_index]

        if (
            current_player.profession == "暴力拆弹专家"
            and current_player.skill_activated
        ):
            width = max(1, min(width, 100))
            current_player.skill_activated = False
        else:
            width = max(1, min(width, 30))
        __width = width
        desc = "\n没什么有趣的事情发生..."
        event_result = self.random_event(width)

        if event_result is not None:
            __width, __desc = event_result
            desc = ""
            for d in __desc:
                desc += "\n" + self.Events_desc[d].format(name=current_player.name)

        current_player.triggered_event = desc
        current_player.width = __width

        self.fuse -= __width + self.correction_value
        if self.correction_value != 0:
            self.correction_value = 0

        if self.fuse <= 0:
            if self.stable:
                self.fuse = random.randint(1, 10)
            else:
                self.game_end()
                return current_player, True

        self.stable = False

        self.current_index += 1
        return current_player, False

    def random_event(self, width: int) -> tuple[int, list[str]] | None:
        result_desc = []
        result = width

        basis = random.randint(0, 100)
        if basis == 0:
            result = 99999999
            result_desc.append("boom")
        elif basis <= 5:
            result = 0
            result_desc.append("skip")
        else:
            basis = random.randint(0, 100)
            if basis <= 10:
                result = result // 2
                result_desc.append("halved")
            elif basis <= 20:
                result *= 2
                result_desc.append("intense")

            basis = random.randint(0, 100)
            if basis <= 10:
                half_of_fuse = self.fuse // 2
                result += random.randint(-half_of_fuse, half_of_fuse)
                result_desc.append("big random")
            elif basis <= 80:
                result += random.randint(-5, 5)
                result_desc.append("random")

        if len(result_desc) == 0:
            return None
        return result, result_desc

    def game_end(self):
        self.__current_index = 0
        self.stable = False
        self.correction_value = 0
        self.init_fuse()

        priority_list = [i for i in range(len(self.players_list))]
        for player in self.players_list:
            player.priority = priority_list.pop(
                random.randint(0, len(priority_list) - 1)
            )
            player.skill_activated = False
            player.skill_freeze = False
            player.profession = None

        professional_number = len(self.players_list) // 4
        professional_players = self.get_random_players(professional_number)
        profession_list = [
            p for p in Bomb_disposal_player.professions.keys() if p != None
        ]
        for i in range(professional_number):
            if len(profession_list) == 0:
                break
            professional_players.pop(
                random.randint(0, len(professional_players) - 1)
            ).profession = profession_list.pop(
                random.randint(0, len(profession_list) - 1)
            )
        self.players_list.sort(key=lambda x: x.priority)

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
        game = Bomb_disposal_Game_instances.get(game_id)

        if command == None:
            if not game:
                return CMDResult("游戏没有开始")

            try_get_player = game.get_player(user_id)
            if try_get_player is None:
                return CMDResult("你没有参与游戏!")

            current_player = game.get_current_player()
            if current_player is None:
                return CMDResult("游戏没有参与者")

            if current_player.id != user_id:
                return CMDResult("不是你的回合")

            player, result = game.play(int(args[0]))
            if not player:
                return CMDResult("游戏中没有参与的玩家，请先加入游戏")
            elif result:
                return CMDResult(
                    (
                        f"---"
                        f"{player.triggered_event}\n"
                        "---\n"
                        f"{player.name}拆除了{player.width}! 💥BOOOOOOOOOOM💥 炸弹爆炸了!\n\n"
                        f"新的排名是:\n {game.get_players_str()}"
                    ),
                    [player.id],
                )
            else:
                return CMDResult(
                    (
                        "---"
                        f"{player.triggered_event}\n"
                        "---\n"
                        f"{player.name}拆除了{player.width}\n"
                        "下一位: "
                    ),
                    [game.players_list[game.current_index].id],
                )

        elif command == "技能":
            if not game:
                return CMDResult("游戏没有开始")
            try_get_player = game.get_player(user_id)
            if try_get_player is None:
                return CMDResult("你没有参与游戏!")
            if try_get_player.profession == None:
                return CMDResult("你还没有职业，无法发动技能!")
            desc = try_get_player.activate_skill(
                game, args[0] if len(args) > 0 else None
            )
            return CMDResult(desc)

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

            current_player = game.get_current_player()
            if current_player is None:
                return CMDResult("游戏没有参与者")

            return CMDResult(
                game.get_players_str() + "\n当前回合玩家: " + current_player.name
            )

        elif command == "跳过":
            if not game:
                return CMDResult("游戏没有开始")
            current_player = game.get_current_player()
            if current_player is None:
                return CMDResult("游戏没有参与者")
            game.skip_player()
            return CMDResult(
                f"{user_name}使用命令跳过回合。下一位: ",
                [current_player.id],
            )

        elif command == "踢出":
            if not game:
                return CMDResult("游戏没有开始")
            if not at_list:
                return CMDResult("请指定要踢出的玩家(At他/她)")
            for at in at_list:
                if at["id"] not in [player.id for player in game.players_list]:
                    return CMDResult(f"{at['name']}都没参加游戏你踢别人干嘛?")
                game.remove_player(at["id"])
            return CMDResult(
                (
                    f"{'、'.join([player['name'] if player['name'] else '未知名称' for player in at_list])} 被踢出游戏。\n"
                    f"当前游戏人数: \n{len(game.players_list)}"
                )
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
            Bomb_disposal_Game_instances[guild_id] = cls()
            return CMDResult("游戏开始")

        elif command == "身份":
            profession_list = (
                p for p in Bomb_disposal_player.professions.keys() if p != None
            )
            result = "身份介绍:\n"
            for p in profession_list:
                result += f"{p}: {Bomb_disposal_player.professions[p]['desc']}\n"
            return CMDResult(result)

        elif command == "设置":
            if not game:
                return CMDResult("游戏没有开始")
            if len(args) == 2 and args[0].isdigit():
                game.set_fuse_limit(int(args[0]), int(args[1]))
                return CMDResult(f"引信范围设置成功: {game.fuse_limit}")
            else:
                return CMDResult("请输入正确的参数")

        elif command == "结束":
            if not game:
                return CMDResult("游戏没有开始")
            del Bomb_disposal_Game_instances[guild_id]
            return CMDResult("游戏结束")

        elif command == "重置":
            if not game:
                return CMDResult("游戏没有开始")
            Bomb_disposal_Game_instances[guild_id].clear()
            return CMDResult("重置成功")

        return CMDResult("未知的游戏命令")


Bomb_disposal_Game_instances: dict[str, BombDisposalGame] = {}
