"""Model loader and aggregator.

Designed not to block main thread.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from threading import Thread
from typing import Callable, Protocol

import httpx
from nonebot import logger
from PIL import Image

from nonebot_plugin_nsfw.config import (
    DEFAULT_NSFW_MODEL_PATH,
    DEFAULT_NSFW_MODEL_URI,
    T_AVAILABLE_MODEL,
    config,
)


class run_model_intf(Protocol):
    def __call__(self, images: Image.Image | list[Image.Image]) -> bool:
        raise NotImplementedError


def _dummy(*args, **kwargs):  # type: ignore
    raise RuntimeError


def get_run_model() -> run_model_intf:
    if _run_model == _dummy:
        raise RuntimeError("no model available")
    return _run_model


_run_model: run_model_intf = _dummy


def load_safety_checker() -> None:
    try:
        from safety_checker import SafetyChecker
    except ImportError as e:
        raise ImportError(
            "safety-checker is not available, install it using "
            '"pip install nonebot-plugin-nsfw[safety-checker]"'
        ) from e
    safety_checker = SafetyChecker.from_pretrained_default()
    safety_checker = safety_checker.to(config.device)
    global _run_model
    _run_model = lambda images: safety_checker.run(images)


def _download_default_nsfw_model() -> None:
    if os.path.exists(DEFAULT_NSFW_MODEL_PATH):
        return
    logger.info(f"Start downloading {DEFAULT_NSFW_MODEL_URI}")
    r = httpx.get(DEFAULT_NSFW_MODEL_URI, follow_redirects=True, timeout=10)
    if r.status_code != 200:
        raise RuntimeError(f"retcode != 200: {r.content}")
    with open(DEFAULT_NSFW_MODEL_PATH, "wb") as f:
        f.write(r.content)
    logger.info(f"Saved model at {DEFAULT_NSFW_MODEL_PATH}")


def load_nsfw_model() -> None:
    # let tensorflow only logs error message
    # os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"  # should be declared in user main
    try:
        from nonebot_plugin_nsfw.vendor_nsfw_model import classify_from_pil, load_model
    except ImportError as e:
        raise ImportError(
            "nsfw-model is not available, install it using "
            '"pip install nonebot-plugin-nsfw[nsfw-model]"'
        ) from e
    model_path = config.nsfw_model_path
    if model_path is not None and not Path(model_path).exists():
        # provide config but not found
        raise FileNotFoundError(f"{model_path} not exist")
    if model_path is None:
        model_path = DEFAULT_NSFW_MODEL_PATH
        _download_default_nsfw_model()
    model = load_model(model_path)
    global _run_model
    # remove the fuck root handler added by model's compiled code
    for handler in logging.root.handlers:
        if isinstance(handler, logging.StreamHandler):
            logging.root.removeHandler(handler)
    _run_model = lambda images: classify_from_pil(model, images)


_loaders: dict[T_AVAILABLE_MODEL, Callable[[], None]] = {
    "safety_checker": load_safety_checker,
    "nsfw_model": load_nsfw_model,
}
_loader = _loaders.get(config.model)
if _loader is None:
    raise RuntimeError(f"unsupported model {config.model!r}")


def _ctx_loader():
    logger.info("Start loading model...")
    _loader()
    logger.success("Successfully load model")


def run_loader_thread() -> Thread:
    th = Thread(target=_ctx_loader)
    th.start()
    return th
