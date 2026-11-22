---
name: claude-environment-checklist
description: 打开 Claude 使用环境检查手帖，按条目核对公网出口、配置、记忆、外接工具、会话或浏览器网站数据。适用于用户要打开手帖、排查 Claude 使用环境或运行本机只读审计时。
---

# Claude 使用环境检查手帖

## 打开网页

用户直接调用技能、要求打开手帖或询问从哪里开始时，用当前环境的浏览器打开[在线手帖](https://huangserva.github.io/claude-environment-checklist/)。只调用技能时打开首页，让用户选择检查项。用户指定了问题时，直接打开对应条目。

- 网络线路和公网出口 → [Claude 公网出口](https://huangserva.github.io/claude-environment-checklist/#network-egress)。
- 用户身份、记忆、指令文件和外接工具 → [配置、记忆与身份来源](https://huangserva.github.io/claude-environment-checklist/#identity-context)。
- 浏览器登录数据 → [浏览器会话](https://huangserva.github.io/claude-environment-checklist/#browser-data)。

在线手帖无法加载时，打开仓库里的 [index.html](../../../index.html)。当前环境无法控制浏览器时，直接把对应链接交给用户。报告页面是否已打开，以工具实际结果为准。

## 运行本机只读审计

打开或浏览手帖时只打开网页。用户明确要求执行本机审计时，以本技能文件所在目录为基准找到仓库里的 [audit_context.py](../../../audit_context.py)。确认脚本在目标电脑运行，并能读取 Claude 实际工作的项目目录，再执行下面的命令。尚未确定目标项目时，先确认目标路径。

```bash
python3 -B "/脚本的绝对路径/audit_context.py" --project "/Claude实际工作的项目目录"
```

`-B` 禁止写入 Python 字节码缓存，`--project` 指定被检查的项目。Windows PowerShell 使用 `py -3 -B` 指定 Python 3。全部检查保持只读，保留原文件、登录状态与会话。

汇总每项发现的来源、状态和下一步核对入口，避免回显文件正文、凭据或会话内容。静态配置只能说明某个来源存在或已声明，实际加载和连接以会话证据为准。公网出口和浏览器会话按手帖的对应页面核对。
