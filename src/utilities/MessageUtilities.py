from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
)
from typing import TypeGuard


def is_group_message(massage_event: MessageEvent) -> TypeGuard[GroupMessageEvent]:
    return massage_event.message_type == "group"


def is_private_message(massage_event: MessageEvent) -> TypeGuard[PrivateMessageEvent]:
    return massage_event.message_type == "private"
