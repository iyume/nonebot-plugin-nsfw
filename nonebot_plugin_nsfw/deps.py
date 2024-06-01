import asyncio
import dataclasses
import os
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, TypeVar

import httpx
from nonebot import logger
from nonebot.adapters.onebot.v11.event import Event, MessageEvent
from nonebot.adapters.onebot.v11.message import Message
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


async def get_images(event: MessageEvent) -> List[Image.Image]:
    """获取 event 内所有的图片，返回 list。"""
    msg_images = event.message["image"]
    images: list[Image.Image] = []
    for seg in msg_images:
        url = seg.data["url"]
        r = httpx.get(url, follow_redirects=True)
        if not r.is_success:
            logger.error(f"Cannot fetch image from {url} msg#{event.message_id}")
            continue
        images.append(Image.open(BytesIO(r.content)))
    return images


async def detect_nsfw(event: MessageEvent) -> bool:
    """依赖注入检查 nsfw 内容。

    通过父依赖来设置 group 或其他 message event。
    """
    run_model = get_run_model()
    images = await get_images(event)
    if not images:
        return False
    loop = asyncio.get_running_loop()
    fut = loop.run_in_executor(
        None,
        lambda: _add_context(run_model, event.message_id)(images),
    )
    have_nsfw = await fut
    await _process_images(event, images, have_nsfw)
    return any(have_nsfw)


async def _process_images(
    event: MessageEvent, images: List[Image.Image], have_nsfw: List[bool]
) -> None:
    if config.save_image:
        save_path = Path(config.image_save_path)
        if not save_path.exists():
            save_path.mkdir(exist_ok=True, parents=True)
        if not save_path.is_dir():
            logger.error(f"Configured {save_path} is not directory")
            return
        nsfw_images = [i[0] for i in zip(images, have_nsfw) if i[1]]
        for i, image in enumerate(nsfw_images):
            image.save(save_path / f"{event.message_id}_{i}.png")


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
