import re
from html import escape, unescape

from nonebot.adapters.onebot.v11.event import (
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from nonebot.adapters.onebot.v11.message import MessageSegment, Message
from nonebot.adapters.onebot.v11 import Bot

from src.plugins.command.scr.calculator.calculator import Calculator, Calculators
from src.plugins.command.scr.holidays import HolidayCalculation as HolidayCal
from src.plugins.command.scr.guessAbbreviation import (
    AbbreviationCommandParser as Abbreviation,
)
from src.plugins.dice.dice import DiceAction
from src.plugins.mini_game.torture_game import TortureGame
from src.plugins.mini_game.russian_roulette_game import RouletteGame
from src.plugins.mini_game.bomb_disposal_game import BombDisposalGame
from src.plugins.command.scr.CMDResult import CMDResult
from typing import Callable, Any, TypedDict, Generic, TypeVar, TypeGuard, Union


T = TypeVar("T", bound=MessageEvent)


def is_group_message(cmd: "Command") -> TypeGuard["Command[GroupMessageEvent]"]:
    return cmd.data.message_type == "group"


def is_private_message(cmd: "Command") -> TypeGuard["Command[PrivateMessageEvent]"]:
    return cmd.data.message_type == "private"


class Command(Generic[T]):
    Command_Pattern = r"^/(\w+)(?:@(\w+))?(?: (.+))?$"

    def get_args(self, message: str):
        if not message.startswith("/"):
            return None
        match = re.match(self.Command_Pattern, message)
        if not match:
            return None
        command, guide, args = match.groups()
        _pure = args.strip() if args else None
        if not command:
            return None
        if (
            isinstance(command, str)
            and isinstance(guide, str | None)
            and isinstance(args, str | None)
        ):
            args = args.split() if args else []
            return command, guide, args, _pure

    def __init__(self, bot: Bot, data: T) -> None:
        self.bot = bot
        self.data = data
        self.command, self.guide, self.args, self.pure = (
            None,
            None,
            [],
            None,
        )
        self.at_list: list[dict[str, str | None]] = []
        at_list = data.original_message.get("at")
        for at in at_list:
            item: dict[str, str | None] = {
                "id": at.data.get("id"),
                "name": at.data.get("name"),
            }
            self.at_list.append(item)

        text = unescape(data.original_message.extract_plain_text())

        get_args = self.get_args(text)
        if not get_args:
            return
        self.command, self.guide, self.args, self.pure = get_args

    async def send(self, result: CMDResult | Message | MessageSegment | str):
        if not isinstance(result, CMDResult):  # 如果不是CMDResult则可以直接发送
            if isinstance(result, str):
                result = escape(result)
            await self.bot.send(self.data, result)
            return
        if result.message:
            await self.bot.send(self.data, result.message)
            return
        message = Message()
        if result.text:
            if isinstance(result.text, str):
                message.append(MessageSegment.text(escape(result.text)))
            else:
                for t in result.text:
                    message.append(MessageSegment.text(escape(t) + "\n"))
        if result.at_list:
            for at in result.at_list:
                if not message:
                    message = Message(MessageSegment.at(at))
                message += MessageSegment.at(at)
                message += MessageSegment.text(" 🔹 ")
        await self.bot.send(self.data, message)

    async def run(self) -> None:
        if not self.command:
            return None
        get_command = CommandStrategy.get_command(self.command)
        if get_command:
            _, strategy = get_command
            return await strategy["strategy"](self)
        else:
            return None


class CommandItem(TypedDict):
    tags: set[str]
    strategy: Callable[[Command], Any]
    desc: str


class CommandStrategy:
    @staticmethod
    async def DiceHandler(cmd: Command) -> None:
        if len(cmd.args) == 1:
            dices = cmd.args[0]
            await cmd.send(
                Message()
                + MessageSegment.at(cmd.data.get_user_id())
                + f"你的掷点结果是：{DiceAction(dices).result}"
            )
        else:
            await cmd.send(MessageSegment.text("请输入掷点指令，如：/d 2d6+3"))

    @staticmethod
    async def TortureGame(cmd: Command):

        if is_group_message(cmd):
            user_nike = cmd.data.sender.nickname
            user_name = user_nike if user_nike else f"Q号: {cmd.data.get_user_id()}"
            result = TortureGame.command_handler(
                command=cmd.guide,
                guild_id=str(cmd.data.group_id),
                user_id=cmd.data.get_user_id(),
                user_name=user_name,
                args=cmd.args,
                at_list=cmd.at_list,
            )
            await cmd.send(result)
        else:
            await cmd.send("请在群组内使用该命令")
            return

    @staticmethod
    async def RouletteGameHandler(cmd: Command):
        if is_group_message(cmd):
            user_nike = cmd.data.sender.nickname
            user_name = user_nike if user_nike else f"Q号: {cmd.data.get_user_id()}"
            result = RouletteGame.command_handler(
                command=cmd.guide,
                guild_id=str(cmd.data.group_id),
                user_id=cmd.data.get_user_id(),
                user_name=user_name,
                args=cmd.args,
                at_list=cmd.at_list,
            )
            await cmd.send(result)
        else:
            await cmd.send("请在群组内使用该命令")
            return

    @staticmethod
    async def BombDisposalGameHandler(cmd: Command):
        if is_group_message(cmd):
            user_nike = cmd.data.sender.nickname
            user_name = user_nike if user_nike else f"Q号: {cmd.data.get_user_id()}"
            result = BombDisposalGame.command_handler(
                command=cmd.guide,
                guild_id=str(cmd.data.group_id),
                user_id=cmd.data.get_user_id(),
                user_name=user_name,
                args=cmd.args,
                at_list=cmd.at_list,
            )
            await cmd.send(result)
        else:
            await cmd.send("请在群组内使用该命令")
            return

    @staticmethod
    async def CalculatorHandler(cmd: Command):
        """文本计算器命令处理"""
        if cmd.guide == "查看任务":
            # 查看当前任务 如果耗时较长此命令将列出，当没有对用户开放，因为用户一般被限制了计算资源
            task = Calculators.get(cmd.data.get_user_id())
            await cmd.send(task.result if task else "你没有下达计算任务")
            return
        elif cmd.guide == "h" or cmd.guide == "help":
            # 帮助 命令格式为: /cal@h [分类名]
            if len(cmd.args) == 1:
                # 按分类获取帮助 键值为传入cmd对象的参数的第一位
                text = Calculator.get_help(cmd.args[0])
                await cmd.send(text)
            elif len(cmd.args) == 0:
                await cmd.send(Calculator.get_help())
            else:
                await cmd.send("请输入帮助指令，如：`/cal@h 符号` 请不要输入其他参数。")
            return
        elif cmd.guide and re.match(r"^d|date$", cmd.guide, re.I) and cmd.pure:
            # 将日期逻辑交给计算器类，通过计算器类，转到日期计算器类
            dateCal = Calculator.date_cal(cmd.pure)
            await cmd.send(str(dateCal))
            return
        elif (
            cmd.guide
            and re.match(r"^c|m|货币|currency|money$", cmd.guide, re.I)
            and cmd.pure
        ):
            # 将货币逻辑交给计算器类，通过计算器类，转到货币计算器类
            currency = Calculator.currency_cal(cmd.pure)
            await cmd.send(str(currency))
            return
        elif cmd.guide == None and len(cmd.args) > 0:
            original_message = unescape(cmd.data.original_message.extract_plain_text())
            match = re.match(r"^/(?:计算|cal\s)(.+)$", original_message)
            message = match.group(1) if match else None
            if not message:
                await cmd.send("命令错误，请输入`/cal h`查看帮助")
                return
            args = re.split(r"(?:!|！)(?:,|，)", message)
            expression = args[0]
            cal = Calculator(expression, cmd.bot, cmd.data, args[1:])
            # source = re.sub(r"^/(?:计算|cal)\s", "", cmd.data.message.content)
            cal.run()

    @staticmethod
    async def HolidaysHandler(cmd: Command):
        holidays_tips = "请输入正确的参数。"

        including_weekends = False
        including_current = False
        if cmd.guide == "周末":
            including_weekends = True
        if cmd.guide == "当前":
            including_current = True

        if len(cmd.args) == 0:
            holidays_tips = HolidayCal.get_holiday_tips(
                including_weekends=including_weekends,
                including_current=including_current,
            )
        elif len(cmd.args) == 1:
            holidays_tips = HolidayCal.get_holiday_tips(
                cmd.args[0],
                including_weekends=including_weekends,
                including_current=including_current,
            )
        await cmd.send(holidays_tips)

    @staticmethod
    async def AbbreviationHandler(cmd: Command):
        if cmd.pure:
            await cmd.send(str(Abbreviation(cmd.pure)))
        else:
            await cmd.send("请输入缩写指令，如：/sx yyds")

    @staticmethod
    async def HelpHandler(cmd: Command):
        help_text = "❗️说明中如果出现方括号`[]`，表示该部分是可选的❗️\n❗️说明中如果出现尖括号`< >`，表示该部分是括号内含义的内容，是必选的。❗️\n❗️说明中的 ` 符号是引用，它不用输入到命令中❗️\n🔹命令由四部分组成\n🔹分别是 `/` + `<命令>` + `[@ + 功能词]` + `[参数]`\n🔹如 `/dice 1d20`\n🔹例子中的`[@ + 功能词]`因为是可选的，所以没有输入\n🔹所以例子中只包括`/` `<命令>` `[参数]`这三部分。\n♾️♾️♾️♾️♾️♾️♾️♾️♾️♾️♾️♾️♾️♾️♾️♾️♾️♾️♾️\n\n"
        if cmd.guide:
            get_command = CommandStrategy.get_command(cmd.guide)
            if not get_command:
                await cmd.send(f"{cmd.guide} 命令不存在")
                return

            cmdStr, cmdItem = get_command

            await cmd.send(
                help_text + CommandStrategy.get_command_help(cmdStr, cmdItem)
            )
            return
        # !内容太多，所以只发送主要帮助
        get_command = CommandStrategy.get_command("help")
        if not get_command:
            raise Exception("help 命令不存在")
        cmdStr, cmdItem = get_command
        help_text += CommandStrategy.get_command_help(cmdStr, cmdItem)
        # help_text += "\n🔹♾️♾️♾️🔺♾️♾️♾️🔹\n\n".join(
        #     [
        #         CommandStrategy.get_command_help(k, v)
        #         for k, v in CommandStrategy.Command_Map.items()
        #     ]
        # )
        await cmd.send(help_text)
        return

    @classmethod
    def get_command_help(cls, name: str, command: CommandItem) -> str:
        return f"✨️🎈\n`/{name}` 别名: {','.join(['`{}`'.format(k) for k in command['tags']])}\n{command['desc']}"

    @classmethod
    def get_command(cls, command: str) -> tuple[str, CommandItem] | None:
        strategy = CommandStrategy.Command_Map.get(command)
        if strategy:
            return command, strategy
        else:
            for cmd, item in CommandStrategy.Command_Map.items():
                if command in item["tags"]:
                    return cmd, item

    Command_Map: dict[str, CommandItem] = {
        "help": {
            "tags": {"h"},
            "strategy": HelpHandler,
            "desc": "帮助命令。显示命令帮助\n使用 `/h@<命令名称>` 显示目标命令的帮助。\n当前可用命令名称: help | dice | 计算 | 假期 | 拷打 | 轮盘 | 拆弹",
        },
        "dice": {
            "tags": {"d"},
            "strategy": DiceHandler,
            "desc": "掷点命令。\n输入 `/dice [n]D<s>[ + n][ + [n]D<s>]` (即 `/d <参数>`)进行点数掷点\n如 `/dice 2d6` 掷两次6面骰子、`/dice 2d6 + 2d6` 掷两次6面骰子，再掷一次2面骰子，`/dice 3d6 + 5` 表示掷三次6面骰子，然后结果+5。\n`/dice 1d4 + d20` 表示掷一次4面骰子，再掷一次20面骰子。",
        },
        "拷打": {
            "tags": {"torture"},
            "strategy": TortureGame,
            "desc": "拷打游戏。\n`/拷打@开始` 开始游戏\n`/拷打@结束` 结束游戏\n`/拷打@重置` 重新开始报名\n`/拷打@查看` 展示参与游戏的玩家\n`/拷打@加入` 加入游戏\n`/拷打@离开` 离开游戏\n`/拷打@踢出 <At踢出的人>` 踢出所At的玩家\n`/拷打@设置 <n>` 设置骰子面数(n)\n`/拷打@设置 <n>V<m>` 设置拷问者人数(n)和被拷问的人数(m)，`V`可以大写也可以小写\n`/拷打` 掷点。",
        },
        "轮盘": {
            "tags": {"roulette"},
            "strategy": RouletteGameHandler,
            "desc": "俄罗斯轮盘游戏。\n`/轮盘@开始` 开始游戏\n`/轮盘@结束` 结束游戏\n`/轮盘@重置` 重新开始报名\n`/轮盘@查看` 展示参与游戏的玩家\n`/轮盘@加入` 加入游戏\n`/轮盘@离开` 离开游戏\n`/轮盘@跳过` 跳过当前一轮回合\n`/轮盘@踢出 <At踢出的人>` 踢出所At的玩家\n`/轮盘@设置 <n>` 设置初始骰子面数(n)\n`/轮盘` 掷点。",
        },
        "拆弹": {
            "tags": {"bombDisposal"},
            "strategy": BombDisposalGameHandler,
            "desc": "💣️拆弹博弈游戏。💣️\n玩家按随机(第一局按加入顺序)顺序进行拆弹，💣️有一个在一定范围内随机长度的引信，玩家通过输入一个命令拆除一定的长度，当💣️的引信小于等于0时，💣️爆炸，游戏结束。\n第一轮没有特殊身份，从第二轮开始，玩家总数的四分之一将随机获取身份，请输入`/拆弹@身份`查看全部可能得身份和技能介绍。\n命令:\n`/拆弹@开始` 开始游戏\n`/拆弹@结束` 结束游戏\n`/拆弹@重置` 重新开始报名\n`/拆弹@查看` 展示参与游戏的玩家\n`/拆弹@加入` 加入游戏\n`/拆弹@离开` 离开游戏\n`/拆弹@跳过` 跳过当前一轮回合\n`/拆弹@踢出 <At踢出的人>` 踢出所At的玩家\n`/拆弹@设置 <n1> <n2>` 设置引信的长度随机范围(n1 ~ n2)\n`/拆弹@身份`查看全部可能的身份。\n`/拆弹@技能`发动身份技能\n`/拆弹 <长度>` 拆弹操作，拆除<长度>长度的炸弹引信(在 1 ~ 30 之间，小于或超出范围将为1或30)。",
        },
        "计算": {
            "tags": {"cal"},
            "strategy": CalculatorHandler,
            "desc": "计算器，遵循python运算符，输入 `/计算@h` 或者 `/cal@h` 查看全部的详细帮助。\n或使用`/cal@h [分类]`  查看分类帮助 例如:`/cal@h 其他`，目前支持的分类: `帮助` `汇率` `日期` `符号` `其他`",
        },
        "假期": {
            "tags": {"holidays"},
            "strategy": HolidaysHandler,
            "desc": "假期提示\n格式: `/假期[@周末|当前] [日期]` 告诉你某天是假期不是假期，如果不是则提示距离上一个假期的时间和距离下一个假期的时间\n输入 `/假期` 则是以当前日期为基准，输入 `/假期 <日期>` 则以输入的日期为基准。\n 如果`/假期@周末` 则假期结果包括周末。\n默认情况下，如果当前已经是假期，则假期结果会返回下次假期是什么时候，如果想要包括当前假期的信息，则用`/假期@当前,` 则假期结果包括当前日期。",
        },
        "abbreviation": {
            "tags": {"缩写", "sx"},
            "strategy": AbbreviationHandler,
            "desc": "猜测缩写意思\n格式: `/sx <缩写>` 或者 `/sx <含缩写的句子>`\n例如: `/sx lsp` => ['老色批', '恋尸癖', ...']",
        },
    }
