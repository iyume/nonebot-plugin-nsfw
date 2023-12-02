import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import Depends

from nonebot_plugin_nsfw.config import config
from nonebot_plugin_nsfw.deps import User, detect_nsfw, get_current_user
from nonebot_plugin_nsfw.loader import run_loader_thread

driver = nonebot.get_driver()
_loader_thread = run_loader_thread()


@driver.on_startup
async def _():
    _loader_thread.join()


nsfw_matcher = on_message()


@nsfw_matcher.handle()
async def _(
    bot: Bot,
    event: GroupMessageEvent,
    has_nsfw: bool = Depends(detect_nsfw),
    user: User = Depends(get_current_user),
):
    if not has_nsfw:
        return
    if config.withdraw:
        await bot.delete_msg(message_id=event.message_id)
    if config.warning_capacity != 0:
        user.warning_count += 1
        await bot.send(event, f"不许色色，警告 {user.warning_count} 次！", at_sender=True)
