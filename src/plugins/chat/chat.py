import time
import asyncio
from typing import TypedDict, Dict, List, Callable, Awaitable, Literal, Any
from openai import AsyncOpenAI
import nonebot
from nonebot.log import logger

from nonebot import require

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler


class ChatEvent:
    def __init__(self, name: str):
        self.name = name
        self.handlers: List[Callable[..., Awaitable[Any]]] = []

    async def trigger(self, *args, **kwargs):
        for handler in self.handlers:
            await handler(*args, **kwargs)

    def add_handler(self, handler: Callable[..., Awaitable[Any]]):
        self.handlers.append(handler)
        return handler


class SessionInfo(TypedDict):
    chat: "Chat"
    last_activity_time: float


SessionDict = dict[str, SessionInfo]


class Chat:
    base_url = "https://api.siliconflow.cn/v1"
    api_key = nonebot.get_driver().config.siliconflow_api_key
    _session_dictionary: SessionDict = {}
    _task_pool: Dict[str, asyncio.Task] = {}

    # 事件定义
    on_message_received = ChatEvent("message_received")
    on_response_received = ChatEvent("response_received")
    on_response_chunk = ChatEvent("response_chunk")
    on_task_complete = ChatEvent("task_complete")
    on_task_error = ChatEvent("task_error")

    @classmethod
    def get_session(cls, session_id: str, type: Literal["group", "private"]):
        if session_id not in cls._session_dictionary:
            cls._session_dictionary[session_id] = {
                "chat": cls(session_id, type),
                "last_activity_time": time.time(),
            }
        return cls._session_dictionary[session_id]

    @classmethod
    def clean_expired_session(cls):
        be_cleaned = []
        for session_id, session_info in cls._session_dictionary.items():
            if time.time() - session_info["last_activity_time"] > 60 * 60 * 2:
                be_cleaned.append(session_id)
        for session_id in be_cleaned:
            del cls._session_dictionary[session_id]

    @classmethod
    async def cancel_all_tasks(cls):
        """取消所有正在运行的任务"""
        for task_id, task in cls._task_pool.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Task {task_id} cancelled")
                except Exception as e:
                    logger.error(f"Error cancelling task {task_id}: {e}")
        cls._task_pool.clear()

    def __init__(self, session_id: str, type: Literal["group", "private"]) -> None:
        self.client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
        self.history = []
        self.session_id = session_id
        self.task_id = 0
        self.type: Literal["group", "private"] = type
        self._non_system_message_count = 0

    async def chat(self, message: str, character: str | None = None) -> str:
        """创建聊天任务并添加到任务池"""
        if self._non_system_message_count == 0 and self.type == "group":
            self.send_system(
                "这是在一个群聊中的多人对话,不同的人有不同的昵称,我会用`<昵称>:`作为不同人说话的前缀,而你是参与这个多人对话中的一员,但是你不用附带昵称输出,直接说出你的要说的话即可"
            )
        if self.type == "group":
            if message != "":
                self.history.append(
                    {"role": "user", "content": f"<{character}>: {message}"}
                )
                self._non_system_message_count += 1
        else:
            if message != "":
                self.history.append({"role": "user", "content": message})
                self._non_system_message_count += 1

        # 触发消息接收事件
        await Chat.on_message_received.trigger(self.session_id, message)

        # 创建任务ID
        self.task_id += 1
        task_id = f"{self.session_id}_{self.task_id}"

        # 创建并启动任务
        task = asyncio.create_task(self._process_chat_task(task_id))
        Chat._task_pool[task_id] = task

        # 等待任务完成并返回结果
        try:
            return await task
        except Exception as e:
            logger.error(f"Chat task {task_id} failed: {e}")
            await Chat.on_task_error.trigger(self.session_id, task_id, str(e))
            return f"聊天请求处理失败: {str(e)}"

    async def _process_chat_task(self, task_id: str) -> str:
        """处理聊天任务"""
        try:
            result = await self._send_request()
            await Chat.on_task_complete.trigger(self.session_id, task_id, result)
            return result
        except Exception as e:
            logger.error(f"Error processing chat task {task_id}: {e}")
            await Chat.on_task_error.trigger(self.session_id, task_id, str(e))
            raise

    async def _send_request(self) -> str:
        """发送API请求并处理响应"""
        Chat._session_dictionary[self.session_id]["last_activity_time"] = time.time()

        # 发送带有流式输出的请求
        result = ""
        try:
            response = await self.client.chat.completions.create(
                model="Qwen/QwQ-32B",
                messages=self.history,
                stream=True,  # 启用流式输出
            )

            async for chunk in response:
                chunk_message = chunk.choices[0].delta.content
                if chunk_message:
                    result += chunk_message
                    # 触发响应块事件
                    await Chat.on_response_chunk.trigger(
                        self.session_id, chunk_message, result
                    )

            # 触发响应完成事件
            await Chat.on_response_received.trigger(self.session_id, result)

            # 添加到历史记录
            self.history.append({"role": "assistant", "content": result})
            self._non_system_message_count += 1
            return result.strip()

        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise

    def clear_history(self):
        self.history = []

    def send_system(self, message: str):
        self.history.append({"role": "system", "content": message})

    @classmethod
    def help(cls):
        return """# 群聊或私聊中,如果没有使用命令,则默认按大模型的ai进行回复,但是在群聊中必须at机器人才能调用ai

## ai相关的命令前缀是"/ai"
- ai相关命令说明:
    1. "/ai help" 显示ai命令帮助
    2. "/ai clean/clear" 两个单词都可以, 清除历史记录
    3. "/ai status" 获取当前ai的状态
    4. "/ai show" 显示所有历史记录的缩略内容
    5. 所有命令的最后一个参数如果是`me`, 则是目标是私有频道的ai, 否则是公共频道的ai, `me`参数在私聊中不可用(因为私聊中不存在公共频道)

## ai的特殊使用规则:
- 在群聊中直接at机器人然后说话, ai会在公共环境下聊天, 即大家一起聊天
- 在群聊中, 如果你at她, 但是前面加上`%`, 则是私有频道(只有你和ai, 和公共频道互不干扰)
- 私有频道和私聊中你与ai的聊天同步, 也就是说, 如果你开始在群里用私有频道和ai聊, 然后来群里at机器人, 使用私有频道(前缀符号"%")继续聊则共享历史, 反之亦然
- 你和ai对话时,如果前缀`system:`, 则发送给ai`system` role 的信息, 一般用作提示词, 默认不会直接发送
- 如果你在发送`system`信息时, 后缀了符号:"$", 则将system直接发给ai,ai会有对应的回复
"""


@scheduler.scheduled_job("cron", hour="*/2", id="regular_chat_cleaning")
async def regular_cleaning():
    nonebot.logger.info("定期清理聊天会话...")
    Chat.clean_expired_session()
    nonebot.logger.info("清理完成")
