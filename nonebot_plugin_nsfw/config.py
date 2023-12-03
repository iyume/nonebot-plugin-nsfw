from pathlib import Path
from typing import Literal, Optional

import nonebot
from nonebot import logger
from pydantic import BaseModel, NonNegativeInt, PositiveInt

DEFAULT_NSFW_MODEL_PATH = str(Path.cwd() / "nsfw_mobilenet2_v1.2.0.h5")
DEFAULT_NSFW_MODEL_URI = "https://github.com/iyume/nonebot-plugin-nsfw/releases/download/v0.1/nsfw_mobilenet2_v1.2.0.h5"

T_AVAILABLE_MODEL = Literal["safety_checker", "nsfw_model"]


class PluginScopedConfig(BaseModel):
    model: T_AVAILABLE_MODEL = "nsfw_model"
    """要使用的模型。默认为 NSFW Model。"""

    device: str = "cpu"

    withdraw: bool = True
    """撤回检测到 NSFW 图片的消息。"""

    nsfw_model_path: Optional[str] = None
    """nsfw-model 模型路径，为 h5 文件或者 SavedModel 目录。
    默认值: `cwd()/nsfw_mobilenet2_v1.2.0.h5`
    """

    warning_capacity: NonNegativeInt = 3
    """一天内警告 N 次后禁言，0 表示不警告，ban=True 则直接禁言。默认为 3."""

    ban: bool = True
    """是否禁言。默认为 True。"""

    ban_time: PositiveInt = 30 * 60  # maybe list of increasing time
    """禁言时长秒数。默认为 1800。"""


class PluginConfig(BaseModel):
    nsfw: PluginScopedConfig


config = PluginConfig.parse_obj(nonebot.get_driver().config).nsfw

if config.nsfw_model_path is not None and config.model != "nsfw_model":
    logger.warning("Provided nsfw_model_path without using its model")
