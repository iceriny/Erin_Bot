from typing import Union
from nonebot.adapters.onebot.v11.message import MessageSegment, Message


class CMDResult:
    def __init__(
        self,
        text: str | list[str] | None = None,
        at_list: list[str] | None = None,
        message: Message | MessageSegment | None = None,
    ):
        self.text = text
        self.at_list = at_list
        self.message = message
