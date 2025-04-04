from nonebot.plugin import PluginMetadata
from nonebot.rule import Rule
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot import get_plugin_config, on_command, on_message, get_driver
from nonebot.params import CommandArg
from typing import Dict, Any

from src.plugins.chat.chat import Chat
from src.plugins.chat.config import Config
from src.utilities.MessageUtilities import is_group_message, is_private_message


__plugin_meta__ = PluginMetadata(
    name="chat",
    description="机器人聊天",
    usage="",
    config=Config,
)
config = get_plugin_config(Config)


async def is_tome(event: MessageEvent) -> bool:
    if is_group_message(event):
        return event.is_tome()
    return is_private_message(event)


command_matcher = on_command("ai", priority=config.command_priority, block=True)
message_matcher = on_message(priority=config.priority, block=False, rule=is_tome)

# 保存正在处理的会话状态
active_sessions: Dict[str, Dict[str, Any]] = {}


# 注册聊天事件处理器
@Chat.on_message_received.add_handler
async def on_message_received(session_id: str, message: str):
    logger.info(f"收到用户消息 [session:{session_id}]: {message}")
    active_sessions[session_id] = {"status": "processing", "message": message}


@Chat.on_response_chunk.add_handler
async def on_response_chunk(session_id: str, chunk: str, current_result: str):
    # 可以在这里实现实时输出，或保存中间状态
    if session_id in active_sessions:
        active_sessions[session_id]["current_result"] = current_result


@Chat.on_response_received.add_handler
async def on_response_received(session_id: str, result: str):
    logger.info(f"响应完成 [session:{session_id}]: {result[:30]}...")
    if session_id in active_sessions:
        active_sessions[session_id]["status"] = "completed"


@Chat.on_task_error.add_handler
async def on_task_error(session_id: str, task_id: str, error: str):
    logger.error(f"聊天任务失败 [session:{session_id}, task:{task_id}]: {error}")
    if session_id in active_sessions:
        active_sessions[session_id]["status"] = "error"
        active_sessions[session_id]["error"] = error


@message_matcher.handle()
async def handle_receive(event: MessageEvent):
    text = event.get_plaintext()
    nike_name = event.sender.nickname if event.sender.nickname else event.get_user_id()
    if is_group_message(event):
        if text.startswith("%"):
            chat_type = "private"
            text = text[1:]
        else:
            chat_type = "group"
        session_id = (
            event.get_user_id() if chat_type == "private" else str(event.group_id)
        )
    else:
        chat_type = "private"
        nike_name = None
        session_id = event.get_user_id()

    # 记录会话开始
    if session_id not in active_sessions:
        active_sessions[session_id] = {"status": "new"}

    chat = Chat.get_session(session_id, chat_type)["chat"]
    return_text = None

    try:
        if text.startswith("system:") or text.startswith("system："):
            chat.send_system(text[7:])
            if text.endswith("$"):
                # 创建系统消息后立即发送请求
                return_text = await chat.chat("")  # 发送空消息触发响应
        else:
            # 启动异步聊天请求
            return_text = await chat.chat(text, nike_name)
    except Exception as e:
        logger.error(f"处理消息异常: {e}")
        return_text = f"处理消息出错: {str(e)}"

    # 清理会话状态
    if session_id in active_sessions:
        del active_sessions[session_id]
    logger.info(f"返回消息: {return_text}")
    await message_matcher.finish(return_text)


@command_matcher.handle()
async def handle_message(event: MessageEvent, args: Message = CommandArg()):
    _args = args.extract_plain_text().strip().split()
    if is_group_message(event):
        chat_type = "private" if _args[-1] == "me" else "group"
        session_id = (
            event.get_user_id() if chat_type == "private" else str(event.group_id)
        )
    else:
        chat_type = "private"
        session_id = event.get_user_id()

    return_text = ""

    # 如果是群聊且最后一个参数是"me"，则剥离最后一个参数`me`
    if is_group_message(event) and _args[-1] == "me":
        _args = _args[:-1]

    if len(_args) == 0:
        return_text = "请输入关于AI的指令"
    elif len(_args) == 1:
        arg = _args[0]
        if arg == "help":
            return_text = Chat.help()
        elif arg == "clean" or arg == "clear":
            chat = Chat.get_session(session_id, chat_type)["chat"]
            chat.clear_history()
            return_text = "历史记录已清空"
        elif arg == "status":
            # 查看当前会话状态
            if session_id in active_sessions:
                status = active_sessions[session_id]["status"]
                return_text = f"当前会话状态: {status}"
            else:
                return_text = "当前没有活动会话"
        elif arg == "cancel":
            # 取消当前任务
            await Chat.cancel_all_tasks()
            if session_id in active_sessions:
                del active_sessions[session_id]
            return_text = "已取消所有正在进行的聊天任务"
        elif arg == "show":
            chat = Chat.get_session(session_id, chat_type)["chat"]
            history = [
                f"{i+1}. {msg['role']} {msg['content'][:20] + '...' if len(msg['content']) > 10 else msg['content']}"
                for i, msg in enumerate(chat.history)
            ]
            if history:
                return_text = "\n".join(history)
            else:
                return_text = "历史记录为空"
            return_text += f"\n当前模型: {Chat.get_model()}"
    elif len(_args) == 2:
        if _args[0] == "setModel":
            if event.get_user_id() == "1179629081":
                Chat.set_model(_args[1])
                return_text = f"已设置模型为{_args[1]}"
            else:
                return_text = "权限不足"

    await command_matcher.finish(return_text)


# 在插件卸载时清理任务
async def _unload():
    logger.info("正在清理聊天任务...")
    await Chat.cancel_all_tasks()


driver = get_driver()
driver.on_shutdown(_unload)
