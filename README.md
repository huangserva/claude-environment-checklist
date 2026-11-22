# Claude 使用环境检查手帖

一份可以离线打开的逐项检查网页。先核对 Claude 的公网出口，再查配置、记忆和身份来源，包括启动时加载的指令、可调用的记忆工具，以及本机状态和备份里的记录。其他项目涵盖完整备份、会话归档、缓存和日志、桌面端数据、命令行凭据及浏览器会话。

## 使用方法

[直接打开使用环境检查手帖](https://huangserva.github.io/claude-environment-checklist/)

1. 从「Claude 公网出口」开始，根据自己的网络环境选择直连、整机代理或分流的核对步骤。使用 Claude Code 命令行时可切到对应步骤。
2. 在检查目录逐项浏览。可手动按说明核对，也可展开「交给 Codex」复制对应指令。

网页本身只展示指南与证据判读。检测站回显代表该次检测请求的出口。要记录为 Claude 线路的实测地址，需要核对两条请求实际经过同一出网节点。清理和迁移按使用者自行确认的范围进行。

## 一条命令运行整合审计

下载 [audit_context.py](https://huangserva.github.io/claude-environment-checklist/audit_context.py) 到本机。从 Claude 实际工作的项目目录运行，可用任意路径存放脚本。以下以下载目录为例。

macOS 或 Linux

```bash
python3 -B "$HOME/Downloads/audit_context.py"
```

Windows 的 PowerShell

```powershell
py -3 -B "$HOME\Downloads\audit_context.py"
```

一次运行有两部分。macOS 先运行从原版 `claude-cleanup` 整合的只读审计，按上游的默认目录和识别规则列出缓存与日志候选、桌面端数据、进程数、遥测设置、精简模式与时区。随后做本手帖的配置、记忆和外接工具检查。Windows 与 Linux 会照常做第二部分，macOS 专用的原版审计标为不适用。

脚本只做只读检查并输出到终端。它不会启动 Claude、运行钩子、连接外接工具、访问网络、备份或删改文件。输出包括路径、字段名、匹配类型和状态。自定义服务端点和认证设置只报告字段名。

在命令后加 `--project 路径` 可指定实际工作目录，`--config-dir 路径` 可指定配置检查使用的 Claude 目录。可以重复使用 `--settings 文件`、`--mcp-config 文件` 和 `--backup-dir 目录` 补查自定义启动配置与备份。加 `--json` 会一起输出两部分的结构化结果。

脚本只做静态核对。文件实际是否加载、工具是否连接、云端账号记忆仍应在对应会话里核验。位于核对范围外或超过读取上限的来源会标成「未核验」。自动识别的身份线索限于常见字段、邮箱格式和身份标签。用手帖第 2 项继续核对项目正文和自定义启动环境。[Claude Code 的指令与记忆说明](https://code.claude.com/docs/en/memory)

### 原版来源

`audit_context.py` 内含原版的只读审计逻辑和版权许可，固定自已核对的 Suyuan 版本。我们沿用原版目录、进程与配置判读规则，并扩展为同时列出匹配位置和未核验状态。公开整合版只提供审计。[原版源码](https://github.com/suyuan2022/suyuan-skill/blob/8babd4557a4774ca8e3d5b784d82f0ee5a4565e5/claude-cleanup/scripts/claude_cleanup.py) · [原版 MIT 许可证](https://github.com/suyuan2022/suyuan-skill/blob/8babd4557a4774ca8e3d5b784d82f0ee5a4565e5/LICENSE)
