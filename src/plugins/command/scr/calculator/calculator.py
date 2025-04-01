import asyncio
import html
import simpleeval as se
import threading
import re

from src.plugins.command.scr.calculator.DateCal import DateCal
from src.plugins.command.scr.calculator.currencyCal import CurrencyCal

from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11 import Bot


class Calculator:
    """
    ## 文本计算器
    输入一个表达式，计算结果
    """

    help_text = {
        "帮助": """\n🟢
该命令与常规命令的参数分割不相同
使用一个叹号加一个逗号分割，不区分中英文标点(eg.`!,")，表达式为第一个参数，后面的参数为`变量名:值`这样的格式
🔹即: `/cal 表达式!,变量名:值!,变量名:值,...`
逗号前后可以存在空格，
变量数量不限制，
变量名基本遵循python的命名规则，但不包括`_`

🔹例如:
`/cal a+b!,a:3!,b:4` => 7
`/cal a+b!,a:你是!,b:谁啊` => 你是谁啊
`/cal x**3+5+x*2!,x:2` => 17  (x的三次方，加5，加x的两倍)
========================================================
""",
        "时间": """\n🟢
计算器支持时间计算
基本命令格式为: `/cal@d 参数` 或者 `/cal@date 参数`
- 🔹根据当前时间计算:
    `/cal@d 1天后`
    `/cal@d 1小时前`
    `/cal@d 1年后3个月后`
- 🔹时间表达式计算:
    时间表达式中，需要用圆括号`()`包裹时间点，用方括号`[]`包裹时间范围，支持加减计算
    🔹例如:
        `/cal@d (2024.5.2) + [50天]` 返回=>`2024年06月21日 00:00:00` 这就是2024年5月2号后50天的时间
        `/cal@d (2025.6.30) - (2024.2.3)` 返回=>`513天` 这就是2025年6月30号减去2024年2月3号的天数
        `/cal@d (2025.6.30) - (2024.2.3) - [1年]` 返回=>`153天` 这就是2025年6月30号减去2024年2月3号减去一年后的天数
    🔺 NOTE: 时间表达式中，如果使用的时间段(即用方括号`[]`包裹的时间范围)参与计算时，如果含有`周`、`月`、`年`以上的单位时，计算结果将会不准确，因为在表达式中，超过天的单位都将使用标准长度，即:一年365天 一月30天 一周7天 一月4周
    🔺 NOTE: 时间表达式计算时，不允许使用 `(时刻)+(时刻)` 这种没有意义的表达式，`(时刻)-[时段]`、`[时段]+[时段]` 这种有意义的才是合法表达式。
""",
        "汇率": """\n🟢
🔹汇率换算:
    格式为: `/cal@c n货币名>换算货币名` 货币名或要转换的货币名可以是货币代码、中文货币名 或者 地区名。
    - 其中`@c`中的c可以换为`m|货币|currency|money`中的任意一个引导
    🔹例如:
        `/cal@c 1USD>CNY` 美元转人民币
        `/cal@货币 3欧元>人民币` 欧元转人民币
        `/cal@m 100英国>美元` 英镑转美元
""",
        "符号": """\n🟢
🔹支持的运算符：
`+ - * /`   加减乘除
`**`	幂运算      x ** y  :  2 ** 10     ->1024
`%`	    模数(余数） x % y   : 15 % 4       ->3
`==`	等于判断    x == y  : 15 == 4      ->False
`< >`   小于、大于
`<=`	小于等于    x <= y  : 1 <= 4       ->True
`>=`	大于等于    x >= y  : 1 >= 4       ->False
`>>`	是右移运算符，将一个数的各二进制位全部右移若干位。例如，x >> y 表示将 x 的二进制表示向右移动 y 位。
`<<`	是左移运算符，将一个数的各二进制位全部左移若干位。例如，x << y 表示将 x 的二进制表示向左移动 y 位。
`^`	    是按位 异或 运算符，对两个数的每个二进制位执行异或操作。如果对应的位相同，则结果为0，否则为1。
`|`	    是按位 或   运算符，对两个数的每个二进制位执行或操作。如果两个对应的位至少有一个为1，则结果为1，否则为0。
`&`	    是按位 与   运算符，对两个数的每个二进制位执行与操作。如果两个对应的位都为1，则结果为1，否则为0。
`~`	    是按位 取反 运算符，对一个数的每个二进制位执行取反操作。即将每个1变为0，每个0变为1。

🔹支持逻辑运算:
`and` 和
`or`  或
`not` 非
========================================================
""",
        "其他": """\n🟢
支持  `if x then y else z` 语法
支持 `in` 语法 "spam" in "my spam" or "spam" in "my breakfast"->False
支持 `[x for x in list]` 语法         eg. => /cal [x+"-" for x in ["你","好","吖"]] -> ['你-', '好-', '吖-']
支持 `"".join(list)` 语法             eg. => /cal "".join([x+"-" for x in ["你","好","吖"]]) -> 你-好-吖-
支持 `"".split(str)` 语法             eg. => /cal "你好吖".split("好") -> ['你', '吖']
支持 `"".replace(str1, str2)` 语法    eg. => /cal "你好吖".replace("你好", "我不好") -> 我不好吖
支持 `"".startswith(str)` 语法
支持 `"".endswith(str)` 语法
支持 `"".find(str)` 语法              eg. => /cal "你好好好好好吖".find("好") -> 1
支持 `"".count(str)` 语法             eg. => /cal "你好好好好好吖".count("好") -> 5

🔹支持的函数:
- randint(a, b)	返回一个随机整数，范围是 [a, b]
- rand()	返回一个随机实数，范围是 [0, 1)
- regRep(pattern, repl, string, count=0, flags=0)
    pattern: 要搜索和替换的模式（正则表达式）。
    repl: 替换后的字符串。
    string: 要进行替换操作的原始字符串。
    count: 可选参数，指定最多替换的次数。默认是 0，表示替换所有匹配。
        eg.1 => `/cal regRep(a,b,o)!,a:你好(?=")!,b:[替换]!,o:我要说"你好"，然后前面的你好会被替换。` -> `我要说"[替换]"，然后前面的你好会被替换。`
""",
    }

    def __init__(
        self, expression: str, bot: Bot, data: MessageEvent, args: list[str]
    ) -> None:
        self.__expression = expression
        """要计算的源码"""
        self.__args = args
        """可选参数"""
        self.calculation_done = asyncio.Event()
        """计算完成的事件"""
        self.lock = threading.Lock()
        """线程锁"""
        self.bot = bot
        """触发计算任务的bot对象"""
        self.data = data
        """触发计算任务的MessageEvent"""
        self.is_err = False
        """计算错误标记"""
        self.err = set()
        """错误信息"""
        Calculators[data.get_user_id()] = self

        self.Eval = se.EvalWithCompoundTypes()
        try:
            self.parse()
        except Exception as e:
            self.is_err = True
            self.err |= {f"||| 错误:[{e}] 错误位置:Calculator.__init__ => parse() |||"}

    def parse(self):
        args_dice = {
            key: value for key, value in (item.split(":") for item in self.__args)
        }
        self.__name: dict[str, str | int | float] = {}
        for k, v in args_dice.items():
            self.__name[k] = self.try_convert_to_number(v)
        self.Eval.names |= self.__name

        self.Eval.functions |= self.get_customize_functions()

    def try_convert_to_number(self, s: str) -> int | float | str:
        try:
            # 尝试转换为整数
            num = int(s)
            return num
        except ValueError:
            try:
                # 尝试转换为浮点数
                num = float(s)
                return num
            except ValueError:
                # 如果无法转换为整数或浮点数，则保持字符串类型
                return s

    def cal(self):
        """计算
        在线程中执行
        """
        self.lock.acquire()
        try:
            self.result = self.Eval.eval(self.__expression)
            self.calculation_done.set()
        except Exception as e:
            self.is_err = True
            self.err |= {f"||| 错误: {e}，错误位置:Calculator.cal() 或计算任务中 |||"}
            self.calculation_done.set()
        finally:
            self.lock.release()

    @staticmethod
    def date_cal(date_expression: str):
        return str(DateCal(date_expression))

    @staticmethod
    def currency_cal(currency_expression: str):
        return str(CurrencyCal(currency_expression))

    async def handle_event(self):
        """
        处理事件结果
        """
        await self.calculation_done.wait()
        msg = (
            f"计算结果：{self.result}"
            if not self.is_err
            else f"{self.err}，输入`/cal help`查看帮助"
        ) + MessageSegment.at(self.data.get_user_id())
        await self.bot.send(self.data, msg)
        # 事件结束后触发
        self.event_end()

    def event_end(self):
        """事件结束后触发，移除计算器对象并取消任务"""
        Calculators.pop(self.data.get_user_id())
        self.task.cancel()

    async def start_event(self):
        """开始事件"""
        # 创建新线程执行计算任务
        thread = threading.Thread(target=self.cal)
        # 线程运行
        thread.start()
        # 启动事件循环
        await self.handle_event()

    def run(self):
        """运行计算"""
        # 获取事件循环，然后创建任务，在任务中执行事件等待结果
        self.task = asyncio.get_event_loop().create_task(self.start_event())

    @classmethod
    def get_help(cls, command: str | None = None):
        """获取帮助信息"""
        text = ""
        if not command:
            for t in cls.help_text.values():
                text += t
        else:
            text = cls.help_text.get(
                command, "未获取到帮助，当前可查看帮助: `帮助` `时间` `符号` `其他`"
            )
        return html.escape(text)

    def get_customize_functions(self):
        """获取自定义函数"""

        def regRep(pattern, repl, string, count=0):
            return re.sub(rf"{pattern}", repl, string, count)

        func_dict = {
            "regRep": regRep,
        }
        return func_dict


Calculators: dict[str, Calculator] = {}
"""储存计算器对象"""
