from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    PluginsName = Literal["chat", "command", "mini_game"]


class PriorityManager:
    """单例模式 插件优先级管理器"""

    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.priority: dict["PluginsName", int] = {
                "chat": 99,
                "command": 0,
                "mini_game": 50,
            }
