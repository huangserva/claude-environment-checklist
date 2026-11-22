# Claude 使用环境检查手帖

一份可以离线打开的逐项检查网页。先核对 Claude 的公网出口，再查配置、记忆和身份来源，包括启动时加载的指令、可调用的记忆工具，以及本机状态和备份里的记录。其他项目涵盖完整备份、会话归档、缓存和日志、桌面端数据、命令行凭据及浏览器会话。

## 使用方法

[直接打开使用环境检查手帖](https://huangserva.github.io/claude-environment-checklist/)

1. 从「Claude 公网出口」开始，根据自己的网络环境选择直连、整机代理或分流的核对步骤。使用 Claude Code 命令行时可切到对应步骤。
2. 在检查目录逐项浏览。可手动按说明核对，也可展开「交给 Codex」复制对应指令。

网页本身只展示指南与证据判读。检测站回显代表该次检测请求的出口。要记录为 Claude 线路的实测地址，需要核对两条请求实际经过同一出网节点。清理和迁移按使用者自行确认的范围进行。

## 配置、记忆和身份来源的只读检测

下载 [audit_context.py](https://huangserva.github.io/claude-environment-checklist/audit_context.py) 到本机。从 Claude 实际工作的项目目录运行，可用任意路径存放脚本。以下以下载目录为例。

macOS 或 Linux

```bash
python3 -B "$HOME/Downloads/audit_context.py"
```

Windows 的 PowerShell

```powershell
py -3 -B "$HOME\Downloads\audit_context.py"
```

脚本只读取可访问的本机文件并输出到终端。它不会启动 Claude、运行钩子、连接外接工具、访问网络或写入文件。输出包括路径、字段名、匹配类型和状态。自定义服务端点和认证设置只报告字段名，身份值、凭据、工具网络地址和文件原文均不出现在输出中。

在命令后加 `--project 路径` 可指定实际工作目录，`--config-dir 路径` 可指定 Claude 配置目录。可以重复使用 `--settings 文件`、`--mcp-config 文件` 和 `--backup-dir 目录` 补查自定义启动配置与备份。加 `--json` 时在终端输出结构化结果。

脚本只做静态核对。文件实际是否加载、工具是否连接、云端账号记忆仍应在对应会话里核验。位于核对范围外或超过读取上限的来源会标成「未核验」。自动识别的身份线索限于常见字段、邮箱格式和身份标签。用手帖第 2 项继续核对项目正文和自定义启动环境。[Claude Code 的指令与记忆说明](https://code.claude.com/docs/en/memory)
