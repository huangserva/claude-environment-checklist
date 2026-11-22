---
name: claude-environment-checklist
description: 使用本项目排查 Claude 环境时，先打开下载项目里的网页手帖，再按用户选定的条目做只读核对。适用于排查 Claude 的公网出口、配置、记忆、外接工具、会话或浏览器网站数据。
---

# Claude 使用环境检查手帖

## 打开网页

以本技能文件的位置为基准，先用浏览器打开下载项目里的 [index.html](../../../index.html)。只调用技能、提供手帖链接或泛泛说「帮我检查一下」时，打开首页，让用户选择检查项。提到具体问题时，在本地网页地址后附上对应条目标识。只有用户明确要求执行一项或多项检查时，才在打开网页后按指定范围开始只读检查。

- 网络线路和公网出口 → [Claude 公网出口](https://huangserva.github.io/claude-environment-checklist/#network-egress)。
- 用户身份、记忆、指令文件和外接工具 → [配置、记忆与身份来源](https://huangserva.github.io/claude-environment-checklist/#identity-context)。
- 浏览器登录数据 → [浏览器会话](https://huangserva.github.io/claude-environment-checklist/#browser-data)。

浏览器无法打开本地文件时，打开[在线手帖](https://huangserva.github.io/claude-environment-checklist/)的对应页面。当前环境无法操作浏览器时，告诉用户在下载文件夹里双击 `index.html` 或给出对应的线上链接。报告页面是否已打开，以工具实际结果为准。

## 运行本机只读审计

用户明确要求执行配置、记忆或外接工具的本机审计时，以本技能文件所在目录为基准找到仓库里的 [audit_context.py](../../../audit_context.py)。这个脚本一次盘点配置、记忆和外接工具，在 macOS 上同时运行原版只读审计。用户只选其中一个范围时，按手帖核对该条目。运行整合脚本前，确认脚本在目标电脑运行，并能读取 Claude 实际工作的项目目录。尚未确定目标项目时，先确认目标路径。

```bash
python3 -B "/脚本的绝对路径/audit_context.py" --project "/Claude实际工作的项目目录"
```

`-B` 禁止写入 Python 字节码缓存，`--project` 指定被检查的项目。Windows PowerShell 使用 `py -3 -B` 指定 Python 3。全部检查保持只读，保留原文件、登录状态与会话。

汇总每项发现的来源、状态和下一步核对入口，避免回显文件正文、凭据或会话内容。静态配置只能说明某个来源存在或已声明，实际加载和连接以会话证据为准。公网出口和浏览器会话按手帖的对应页面核对。
