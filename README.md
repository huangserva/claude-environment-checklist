# Claude 使用环境检查手帖

Claude 连不上、突然知道了旧项目里的信息，或者换机前想确认哪些会话和配置要保留？这套工具帮你按线索查到**请求走了哪条网络线路、信息可能来自哪份文件或哪个工具、备份还有哪些内容可以恢复**。

## 用 Codex 打开手帖

1. 克隆仓库，把仓库目录选为 Codex 当前项目。技能随仓库提供，无需单独安装。已经克隆的用户可以先拉取最新版本。[查看技能文件](.agents/skills/claude-environment-checklist/SKILL.md)
2. 在对话框输入 `$claude-environment-checklist`，选中同名技能，再发送「先打开手帖，等我选检查项」。
3. 网页打开后，先选要查的条目。要请 Codex 执行时，再说清楚要查哪一项。盘点本机配置时，告诉 Codex Claude 实际工作的项目目录。

只把 GitHub 链接贴进对话，Codex 可以阅读网页。要调用仓库技能，请在 Codex 中打开克隆下来的目录。

[打开在线手帖](https://huangserva.github.io/claude-environment-checklist/) · [下载单文件只读检测脚本](https://huangserva.github.io/claude-environment-checklist/#identity-context)

[![Claude 使用环境检查手帖首页，左侧为检查目录，右侧显示公网出口核对步骤](assets/homepage.png)](https://huangserva.github.io/claude-environment-checklist/)

## 遇到什么问题，从哪一项查

| 遇到的问题 | 建议先看 |
| --- | --- |
| Claude 连不上，或者浏览器和终端的公网出口不同 | [公网出口](https://huangserva.github.io/claude-environment-checklist/#network-egress)。对照 Claude 的已有连接与出口检测请求，确认它们实际走的线路。 |
| Claude 知道你没在当前对话里提过的姓名、偏好或旧项目 | [配置、记忆与身份来源](https://huangserva.github.io/claude-environment-checklist/#identity-context)。从指令文件、自动记忆、项目记录、插件和外接工具找来源。 |
| 同一台电脑上的浏览器登录状态不同 | [浏览器会话](https://huangserva.github.io/claude-environment-checklist/#browser-data)。逐个浏览器配置查 Claude 和 Anthropic 的网站数据，另行核验当前登录状态。 |
| 换机、重装，或准备清理本机数据 | [完整备份](https://huangserva.github.io/claude-environment-checklist/#old-backup)和[会话归档](https://huangserva.github.io/claude-environment-checklist/#sessions)。先核对要保留的会话和可恢复的副本。 |

手帖也提供缓存与日志、桌面应用数据和命令行凭据的核对步骤。

## 怎么用

### 打开网页逐项核对

从左侧目录选择你遇到的问题，按该项的步骤操作。也可以展开「交给 Codex」，复制该项的只读核对指令。查公网出口和浏览器网站数据时，从这个入口开始。[打开在线手帖](https://huangserva.github.io/claude-environment-checklist/)

### 下载脚本，一次盘点本机

安装 Python 3 后，将 `audit_context.py` 保存到「下载」目录，从 Claude 实际工作的项目目录打开终端，执行对应命令。[下载脚本](https://huangserva.github.io/claude-environment-checklist/#identity-context)

**macOS 或 Linux**

```bash
python3 -B "$HOME/Downloads/audit_context.py"
```

**Windows PowerShell**

```powershell
py -3 -B "$HOME\Downloads\audit_context.py"
```

`-B` 禁止 Python 写入缓存。Windows 的 `-3` 指定 Python 3。文件保存在其他地方时，替换为实际路径。

在 macOS 上，脚本会同时输出原版 `claude-cleanup` 的本机审计和本项目的配置检查。前者盘点默认目录、缓存、日志、桌面数据和相关进程，后者查配置、记忆和外接工具。Windows 和 Linux 会运行配置检查，原版专用于 macOS 的审计标为「不适用」。

### 怎么判断结果

例如，报告出现下面两行时，说明在全局配置中找到了一个外接记忆工具的声明。是否有连接或调用记录，应回到实际使用的 Claude 会话核对。

```text
【已配置】外接工具 · ~/.claude.json
  用户级 · example-memory · 连接与调用情况未核验
```

脚本只读本机状态，结果只输出到终端。它列出来源、状态和线索类型，凭据原值与文件正文保留在本机。云端账号记忆在账号设置里核对。[Claude Code 指令与记忆说明](https://code.claude.com/docs/en/memory)

<details>
<summary>自定义工作目录、配置路径和输出格式</summary>

| 选项 | 用途 |
| --- | --- |
| `--project 路径` | 指定 Claude 实际工作的目录。 |
| `--config-dir 路径` | 指定配置检查使用的 Claude 目录。原版审计仍盘点 macOS 默认目录。 |
| `--settings 文件`、`--mcp-config 文件` | 补查自定义启动设置和外接工具配置。可以重复指定。 |
| `--backup-dir 目录` | 补查历史配置备份。可以重复指定。 |
| `--json` | 将两部分结果以便于程序读取的结构化格式输出到终端。 |

</details>

## 原版来源

脚本内置 Suyuan 的 `claude-cleanup` 只读审计逻辑，并保留上游版权和许可。[原版源码](https://github.com/suyuan2022/suyuan-skill/blob/8babd4557a4774ca8e3d5b784d82f0ee5a4565e5/claude-cleanup/scripts/claude_cleanup.py) · [原版开源许可](https://github.com/suyuan2022/suyuan-skill/blob/8babd4557a4774ca8e3d5b784d82f0ee5a4565e5/LICENSE)
