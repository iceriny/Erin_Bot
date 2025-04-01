import json
from typing import TypedDict, Literal
import datetime


import chinese_calendar as calendar
from chinese_calendar.constants import Holiday

# if __name__ == "__main__":
#     import sys
#     import os

#     path = os.path.abspath("")
#     print(path)
#     sys.path.append(path)
#     from erin.utilities.DateParser import DateParser

#     sys.path.remove(path)
# else:
#     from erin.utilities.DateParser import DateParser
from src.utilities.DateParser import DateParser

Holiday_Name = {
    Holiday.new_years_day.value: "元旦",
    Holiday.spring_festival.value: "春节",
    Holiday.tomb_sweeping_day.value: "清明",
    Holiday.labour_day.value: "劳动节",
    Holiday.dragon_boat_festival.value: "端午",
    Holiday.national_day.value: "国庆节",
    Holiday.mid_autumn_festival.value: "中秋",
    Holiday.anti_fascist_70th_day.value: "中国人民抗日战争暨世界反法西斯战争胜利70周年纪念日",
}


class HolidayCalculation:
    @classmethod
    def __get_holiday(
        cls, date: datetime.date, including_weekends: bool = False
    ) -> tuple[str | None, str | Literal["双休日"] | None]:
        """
        ### 获取当前时间是不是节假日

        #### :return:
        - 第一个值如果不是`None`就是节假日，第二个值是节假日名称
        - 第一个值如果是`None`就是不是节假日，如果第二个值不是`None` 则是调休日
        """
        date_info = calendar.get_holiday_detail(date)
        on_holiday, holiday_name = date_info

        if holiday_name:
            holiday_name = Holiday_Name[holiday_name]

        if holiday_name is None and on_holiday:
            holiday_name = "双休日"
            if not including_weekends:
                on_holiday = False

        if on_holiday:
            return date.strftime("%Y年%m月%d日"), holiday_name
        else:
            return None, holiday_name

    @classmethod
    def get_holiday(cls, date_str: str | None = None):
        parser = DateParser()
        date = parser(date_str).date()
        date_value, date_name = cls.__get_holiday(date)
        if date_value is None:
            if date_name:
                return f"{date_value}是调休日! 它是为了{date_name}调休哒~"
            return f"{date_value}不是节假日哦。"
        else:
            return f"{date_value}就是节假日了哦，这一天是{date_name}~"

    @classmethod
    def __get_next_holiday(
        cls,
        date: datetime.date,
        including_weekends: bool = False,
        including_current: bool = False,
        *,
        _later: int = 0,
    ):
        """
        ### 获取下一个节假日
        #### :return:
        - 第一个值是下一个节假日的日期
        - 第二个值是下一个节假日的名称
        """
        date_value, date_name = cls.__get_holiday(date, including_weekends)
        if date_value is None:
            including_current = True
        if date_value is None:
            _later += 1
            date += datetime.timedelta(days=1)
            date_value, date_name, _later = cls.__get_next_holiday(
                date, including_weekends, including_current, _later=_later
            )
        else:
            if not including_current:
                _later += 1
                date += datetime.timedelta(days=1)
                date_value, date_name, _later = cls.__get_next_holiday(
                    date, including_weekends, including_current, _later=_later
                )

        return date_value, date_name, _later

    @classmethod
    def __get_previous_holiday(
        cls, date: datetime.date, including_weekends: bool = False, earlier: int = 0
    ):
        """
        ### 获取上一个节假日
        #### :return:
        - 第一个值是上一个节假日的日期
        - 第二个值是上一个节假日的名称
        """
        date_value, date_name = cls.__get_holiday(date, including_weekends)
        if date_value is None:
            earlier += 1
            date -= datetime.timedelta(days=1)
            date_value, date_name, earlier = cls.__get_previous_holiday(
                date, including_weekends, earlier
            )

        return date_value, date_name, earlier

    @classmethod
    def get_previous_holiday(
        cls, date_str: str | None, including_weekends: bool = False
    ):
        parser = DateParser()
        date = parser(date_str).date()
        date_value, date_name, earlier = cls.__get_previous_holiday(
            date, including_weekends
        )
        if earlier == 0:
            return f"今天就是节假日了啦，这一天是{date_name}~"
        else:
            prefix = (
                f"{earlier}天前的{date_value}是"
                if earlier > 2
                else ("昨天才刚过完" if earlier == 1 else "前天才刚过完")
            )
            return f"{prefix}{date_name}呢~"

    @classmethod
    def get_next_holiday(
        cls,
        date_str: str | None = None,
        including_weekends: bool = False,
        including_current: bool = False,
    ):
        parser = DateParser()
        date = parser(date_str).date()
        date_value, date_name, later = cls.__get_next_holiday(
            date, including_weekends, including_current
        )

        if later == 0:
            return f"今天就是节假日了啦，这一天是{date_name}~"
        else:
            if later == 1:
                return_text = "明天" + f"是{date_value}，就是{date_name}啦~ 享受假期吧~"
            elif later == 2:
                return_text = "后天" + f"是{date_value}，就是{date_name}啦~ 享受假期吧~"
            elif later < 7:
                return_text = (
                    f"还有{later}天，在{date_value}时候就是{date_name}咯，不到一周了~"
                )
            else:
                return_text = (
                    f"{later}天后，也就是{date_value}，就是{date_name}咯~ 加油www~"
                )
            return return_text

    @classmethod
    def get_holiday_tips(
        cls,
        date_str: str | None = None,
        including_weekends=False,
        including_current=False,
    ):
        previous_holiday = cls.get_previous_holiday(date_str, including_weekends)
        next_holiday = cls.get_next_holiday(
            date_str, including_weekends, including_current
        )

        result = (
            f"{previous_holiday}\n{next_holiday}"
            if previous_holiday != next_holiday
            else f"{previous_holiday}"
        )
        return result
