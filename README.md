<p align="center">
  <img src="logo/logo.png" width="200" height="200" alt="nonebot-plugin-nsfw">
</p>

<div align="center">

# NoneBot Plugin NSFW

</div>

此插件是一个集成于 NoneBot 的、基于深度神经网络的 **群聊 NSFW 图片检测插件**，带有 **撤回、警告、禁言** 等功能。可选择使用 [Safety Checker](https://github.com/iyume/safety-checker)、[NSFW Model](https://github.com/GantMan/nsfw_model) 模型。

**注意：** 目前插件仅在 matcha 完成测试，只能保证 OneBot V11 兼容。

## Safety Checker 对比 NSFW Model

|                              | Safety Checker      | NSFW Model（默认） |
| ---------------------------- | ------------------- | ------------------ |
| 训练时间                     | 2022                | 2020               |
| 适用情景                     | 仅 R15+             | 仅 R18+            |
| 框架                         | PyTorch             | Tensorflow         |
| 模型大小                     | 600MB (fp16)        | ~10MB (fp16)       |
| 内存占用                     | 1.2GB               | 极小               |
| 执行时间 (CPU Ryzen 7 7840H) | 0.5s (10)           | 0.05s (1)          |
| 执行时间 (GPU 4060 Laptop)   | 0.15s (4060 laptop) | 暂无               |

## 快速开始

插件默认使用 NSFW Model 轻量模型，默认设备为 CPU。

安装 NoneBot：

```txt
pip install nonebot2[fastapi]
```

安装插件：

```txt
pip install nonebot-plugin-nsfw[nsfw-model]
```

将插件直接导入即可使用。

默认行为：检测群聊消息中的图片并自动撤回 nsfw 图片，发送警告消息，警告次数累计 5 次执行禁言。

使用前请确保机器人是管理员身份。

## 使用 Safety Checker

> Safety Checker 由我本人编写，只有 hook diffusers 的版本，暂时没有独立的实现，不过正常使用没问题。也许将来能实现检测强度配置。可参考 https://github.com/iyume/safety-checker/issues/1

Safety Checker 是基于最新最热 CLIP 的 NSFW 图像概念实现。

使用下面命令安装：

```txt
pip install nonebot-plugin-nsfw[safety-checker]
```

此过程会自动下载 torch GPU 版本，大约 2GB。

> 如果你需要仅 CPU 的 torch，需要提前使用这条命令安装 torch：`pip install torch --index-url https://download.pytorch.org/whl/cpu`

第一次加载插件时会从 huggingface 下载一个 600 MB 的模型文件，请确保网络连接通畅。（模型缓存由 huggingface_lab 管理，位置在 `~/.cache/huggingface/hub`）

载入 Safety Checker 需要 **至少 1.2 GB** 内存/显存。
CPU (Ryzen 7 7840H) 每次调用大约耗时 0.5s，图像大小不影响调用耗时。

## 使用 NSFW Model（默认）

NSFW Model 是基于 Inception V3 和 MobileNet V2 的传统视觉模型。

[nsfwjs](https://nsfwjs.com/) 是它的 js 实现，可以进行在线测试。

官方提供了 [多种模型下载地址](https://github.com/GantMan/nsfw_model#download)，但是强烈建议使用默认选项也就是 v1.2.0 模型，因为 v1.1.0 的模型对 r18 图像可能存在误判，上面那个在线测试网页用的大概就是 v1.1.0 的模型。

**注意：** 不同于 pytorch cuda 的一键安装，tensorflow 的 cuda 环境依赖于系统，使用前需要你熟悉 cuda、cuDNN 等概念并完成环境安装。如果你仅用 CPU 那么这是个不错的选择。

使用下面命令安装：

```txt
pip install nonebot-plugin-nsfw[nsfw-model]
```

> 有可能把 NSFW Model 迁移到 PyTorch / NumPy 吗？<br>
> 由于两个平台各种函数实现的略微差异，同一个权重文件表现可能不一致。
> 同理，尝试使用 numpy 去实现也是困难的。
> 目前似乎没看到可以直接完美实现前向计算的轻量库，如果你找到了可以告诉我。

## 插件配置项

|                          | 默认值                            | 可选值                         | 说明                                               |
| ------------------------ | --------------------------------- | ------------------------------ | -------------------------------------------------- |
| nsfw\_\_model            | "nsfw-model"                      | "safety-checker", "nsfw-model" |                                                    |
| nsfw\_\_device           | "cpu"                             | "cpu", "cuda", etc.            |                                                    |
| nsfw\_\_withdraw         | True                              | True, False                    | 撤回检测到 NSFW 图片的消息                         |
| nsfw\_\_nsfw_model_path  | cwd() / nsfw_mobilenet2_v1.2.0.h5 | .h5 or SavedModel path         | nsfw-model 模型路径，没配置则自动下载              |
| nsfw\_\_warning_capacity | 3                                 | 非负整数                       | 一天内警告 N 次后禁言，0 不警告，ban=True 直接禁言 |
| nsfw\_\_ban              | True                              | True, False                    | 是否启用禁言                                       |
| nsfw\_\_ban_time         | 1800                              | 正整数                         | 禁言时长，单位为秒数                               |

更多配置正在开发中...

欢迎 issue 提出问题和想法。
