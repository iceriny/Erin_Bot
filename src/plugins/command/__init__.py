from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.log import logger
from nonebot import get_plugin_config, on_command
from nonebot.plugin import PluginMetadata
from src.plugins.command.config import Config


__plugin_meta__ = PluginMetadata(
    name="command",
    description="处理命令的模块",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)


command_matcher = on_command("cmd", priority=config.command_priority)


@command_matcher.handle()
async def handle_receive(bot: Bot, event: MessageEvent):
    logger.debug(bot.__repr__())
    logger.debug(event.__repr__())
    await command_matcher.finish()
