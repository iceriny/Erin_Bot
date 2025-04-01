from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment
from nonebot.log import logger
from nonebot import get_plugin_config, on_command
from nonebot.plugin import PluginMetadata
from src.plugins.command.config import Config

from src.plugins.command.scr.command import CommandStrategy, Command


__plugin_meta__ = PluginMetadata(
    name="command",
    description="处理命令的模块",
    usage="",
    config=Config,
)

config = get_plugin_config(Config)


key_set = [key for key in CommandStrategy.Command_Map.keys()]
for c in CommandStrategy.Command_Map.values():
    key_set += list(c["tags"])
command_matcher = on_command(
    "cmd", aliases={v for v in key_set}, priority=config.command_priority, block=True
)


@command_matcher.handle()
async def handle_receive(bot: Bot, event: MessageEvent):
    logger.debug(bot.__repr__())
    logger.debug(event.__repr__())
    if event.get_user_id() != "3754114368":
        cmd = Command(bot, event)
        await cmd.run()
    await command_matcher.finish()
