import re
from datetime import datetime, timedelta
from src.utilities.DateParser import DateParser


class DateFormat:
    def __init__(self, date: datetime | timedelta) -> None:
        self._date = date

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        if isinstance(self._date, datetime):
            return self._date.strftime("%Y年%m月%d日 %H:%M:%S")
        else:
            days = f"{self._date.days}天" if self._date.days != 0 else ""
            seconds = f" {self._date.seconds}秒" if self._date.seconds != 0 else ""
            microseconds = (
                f" {self._date.microseconds}毫秒"
                if self._date.microseconds != 0
                else ""
            )
            return days + seconds + microseconds


_DP = DateParser()


class DateCal:
    _INITIAL_DATE = datetime(1970, 1, 1)

    def __init__(self, string: str) -> None:

        match = re.findall(
            r"(\+|-)? ?((?:\(|（).+?(?:\)|）)|(?:\[|【).+?(?:\]|】))", string
        )  # +|- [时段] 或者 (时刻)

        if len(match) == 0:  # 不带括号 按时刻处理
            self.result_time = _DP(string)

        elif len(match) == 1:  # 带括号 但只有一个捕获 按时刻处理
            self.result_time = _DP(string)

        else:  # 如果有多个括号 则是 时间计算
            self.result_time = None  # 时间计算结果
            for symbol, time in match:

                single = None
                if time.startswith("[") or time.startswith(
                    "【"
                ):  # 如果是`[]`包裹 则是时间段
                    # 获取时间段的数值

                    match_time = re.match(
                        r"^\[(?:(\d+)(?:y|year|年))?\s*?(?:(\d+)(?:m|month|月))?\s*?(?:(\d+)(?:w|week|周|星期))?\s*?(?:(\d+)(?:d|day|天|日))?\s*?(?:(\d+)(?:h|hour|(?:小)?时))?\s*?(?:(\d+)(?:m|min|minute|分(?:钟)?))?\s*?(?:(\d+)(?:s|sec|second|秒))?\]$",
                        time,
                    )
                    if match_time:  # 如果匹配到时间段数值
                        groups = match_time.groups()

                        _year = float(groups[0]) if groups[0] else 0
                        _month = (float(groups[1]) if groups[1] else 0) + _year * 12
                        _week = float(groups[2]) if groups[2] else 0
                        _day = (
                            (float(groups[3]) if groups[3] else 0)
                            + _week * 7
                            + _month * 30
                        )
                        _hour = float(groups[4]) if groups[4] else 0
                        _minute = float(groups[5]) if groups[5] else 0
                        _second = float(groups[6]) if groups[6] else 0

                        # 生成时间段对象
                        single = timedelta(
                            days=_day,
                            hours=_hour,
                            minutes=_minute,
                            seconds=_second,
                        )

                    else:
                        raise ValueError("时间段格式错误")
                elif time.startswith("(") or time.startswith("（"):
                    # 如果不是`[]`包裹 则是时刻
                    single = _DP(time)

                else:
                    raise ValueError("进行时间计算时，需要使用包裹器确定是时刻还是时段")

                if not self.result_time:  # 如果是第一个时间(段)
                    self.result_time = single

                else:  # 如果不是第一个时间(段)
                    if isinstance(single, timedelta):
                        # 如果这次的结果也是时段
                        if symbol == "+":
                            self.result_time += single
                        elif symbol == "-":
                            self.result_time -= single
                        else:
                            raise ValueError("时间计算不支持其他符号")

                    elif isinstance(
                        self.result_time, datetime
                    ):  # 如果上次循环的结果是时刻 这次的结果是时刻
                        if symbol == "+":
                            raise ValueError("时间计算不支持日期与日期之间的相加计算")
                        self.result_time -= single

                    elif isinstance(
                        self.result_time, timedelta
                    ):  # 如果上次循环的结果是时段 这次的结果是时刻
                        if symbol == "-":
                            raise ValueError("时间计算不支持日期与时刻之间的相减计算")
                        self.result_time += single

    def __repr__(self) -> str:
        return f"DateCal=>(date_time: {self.result_time})"

    def __str__(self) -> str:
        if self.result_time is None:  # 如果没有计算结果
            return "时间计算失败"
        return str(DateFormat(self.result_time))
