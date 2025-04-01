from pydantic import BaseModel, field_validator

from src.priority_manager import PriorityManager

pm = PriorityManager()


class Config(BaseModel):
    """命令插件的配置信息"""

    priority: int = pm.priority["chat"]
    command_priority: int = pm.priority["command"]
    enabled: bool = True
