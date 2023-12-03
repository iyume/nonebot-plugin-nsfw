import nonebot
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import Depends
from nonebot.plugin import PluginMetadata

from nonebot_plugin_nsfw.config import PluginConfig, config
from nonebot_plugin_nsfw.deps import User, detect_nsfw, get_current_user, get_run_model
from nonebot_plugin_nsfw.loader import run_loader_thread

__plugin_meta__ = PluginMetadata(
    name="群聊 NSFW 图片检测",
    description="群聊 NSFW 图片检测插件，带有撤回、警告、禁言等功能。使用 Safety Checker / NSFW Model",
    usage="无",
    type="application",
    config=PluginConfig,
    homepage="https://github.com/iyume/nonebot-plugin-nsfw",
    supported_adapters={"~onebot.v11"},
    extra={},
)

driver = nonebot.get_driver()
_loader_thread = run_loader_thread()


@driver.on_startup
async def _():
    _loader_thread.join()


def check_model_available() -> bool:
    try:
        get_run_model()
    except ValueError:
        return False
    return True


nsfw_matcher = on_message(rule=check_model_available)


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
    if config.ban == True and user.warning_count > config.warning_capacity:
        await bot.set_group_ban(
            group_id=event.group_id, user_id=event.user_id, duration=config.ban_time
        )
    else:
        await bot.send(event, f"涩涩哒咩，警告 {user.warning_count} 次！", at_sender=True)
