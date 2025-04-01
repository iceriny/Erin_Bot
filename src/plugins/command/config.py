from pydantic import BaseModel, field_validator


class Config(BaseModel):
    """命令插件的配置信息"""
    command_priority: int = 1
    command_enabled: bool = True
