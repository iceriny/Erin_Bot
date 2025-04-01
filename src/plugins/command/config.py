from pydantic import BaseModel
from src.priority_manager import PriorityManager

pm = PriorityManager()


class Config(BaseModel):
    """命令插件的配置信息"""

    command_priority: int = pm.priority["command"]
    command_enabled: bool = True
