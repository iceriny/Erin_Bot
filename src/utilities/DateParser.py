from dateparser.date import DateDataParser
from datetime import datetime, timedelta, date


class DateParser(DateDataParser):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            ["zh-Hans"],
            try_previous_locales=True,
        )

    def __call__(self, date_string: str | None = None):
        if date_string is None:
            return datetime.now()
        date_obj = self.get_date_data(
            date_string,
            [
                "%Y年",
                "%Y年%m月",
                "%Y年%m月%d日",
                "%Y年%m月%d日 %H时",
                "%Y年%m月%d日 %H:%M",
                "%Y年%m月%d日 %H:%M:%S",
            ],
        ).date_obj
        return date_obj if date_obj else datetime.now()

    def format(self, __date: str | datetime | date) -> str:
        if isinstance(__date, str):
            return self(__date).strftime("%Y年%m月%d日 %H:%M:%S")
        if isinstance(__date, datetime):
            time_format_str = ""
        else:
            time_format_str = " %H:%M:%S"
        return __date.strftime(f"%Y年%m月%d日{time_format_str}")
