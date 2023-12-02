import asyncio
import dataclasses
from datetime import date
from io import BytesIO
from typing import Any, Dict, TypeVar

import httpx
from nonebot import logger
from nonebot.adapters.onebot.v11.event import Event, MessageEvent
from PIL import Image

from nonebot_plugin_nsfw.config import config
from nonebot_plugin_nsfw.loader import get_run_model, run_model_intf

TC_RUNNER = TypeVar("TC_RUNNER", bound=run_model_intf)


def _add_context(func: TC_RUNNER, msgid: int) -> TC_RUNNER:
    def _(*args: Any, **kwargs: Any) -> Any:
        logger.debug(f"Start processing images msg#{msgid}")
        res = func(*args, **kwargs)
        if res == True:
            logger.info(f"NSFW image was detected in msg#{msgid}")
        logger.debug(f"Finish msg#{msgid}")
        return res

    return _  # type: ignore


async def detect_nsfw(event: MessageEvent) -> bool:
    """依赖注入检查 nsfw 内容。

    通过父依赖来设置 group 或其他 message event。
    """
    run_model = get_run_model()
    msg_images = event.message["image"]
    images: dict[int, Image.Image] = {}
    for idx, seg in enumerate(msg_images):
        url = seg.data["url"]
        r = httpx.get(url)
        if r.status_code != 200:
            logger.error(f"Cannot fetch image from {url} msg#{event.message_id}")
            continue
        images[idx] = Image.open(BytesIO(r.content))
    if not images:
        return False
    loop = asyncio.get_running_loop()
    fut = loop.run_in_executor(
        None, lambda: _add_context(run_model, event.message_id)(list(images.values()))
    )
    res = await fut
    return res


# TODO: add Annotated deps when upgrade to py39


@dataclasses.dataclass
class User:
    date_: date
    warning_count: int = 0

    def refresh(self) -> None:
        today = date.today()
        if self.date_ == today:
            return
        self.date_ = today
        self.warning_count = 0

    @property
    def should_ban(self) -> bool:
        return self.warning_count > config.warning_capacity


# simple database
users: Dict[str, User] = {}


async def get_current_user(event: Event) -> User:
    user_id = event.get_user_id()
    # implicit register
    if user_id not in users:
        users[user_id] = user = User(date_=date.today())
    else:
        user = users[user_id]
        user.refresh()
    return user
