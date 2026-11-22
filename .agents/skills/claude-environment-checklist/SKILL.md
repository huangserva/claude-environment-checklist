---
name: claude-environment-checklist
description: 使用本项目排查 Claude 环境时，先打开下载项目里的网页手帖，再按用户选定的条目做只读核对。适用于排查 Claude 的公网出口、配置、记忆、外接工具、会话或浏览器网站数据。
---

# Claude 使用环境检查手帖

## 打开网页

先打开下载项目中的本地手帖。第 0 步可用 [本地启动器](../../../launch_checklist.py) 打开，在项目根目录运行 `python3 -B launch_checklist.py`，Windows 使用 `py -3 -B launch_checklist.py`。启动器会打开网页，等用户点击「开始只读检查」才盘点本机。用户只想看手帖时，也可打开 [index.html](../../../index.html)。提到具体问题时，在网页地址后附上对应条目标识。只有用户明确要求执行一项或多项检查时，才按指定范围开始只读检查。

- 一次盘点本机配置、记忆和外接工具 → [第 0 步 · 一键只读检查](https://huangserva.github.io/claude-environment-checklist/#quick-audit)。
- 网络线路和公网出口 → [Claude 公网出口](https://huangserva.github.io/claude-environment-checklist/#network-egress)。
- 用户身份、记忆、指令文件和外接工具 → [配置、记忆与身份来源](https://huangserva.github.io/claude-environment-checklist/#identity-context)。
- 浏览器登录数据 → [浏览器会话](https://huangserva.github.io/claude-environment-checklist/#browser-data)。

浏览器无法打开本地文件时，打开[在线手帖](https://huangserva.github.io/claude-environment-checklist/)的对应页面。当前环境无法操作浏览器时，告诉用户在下载文件夹里双击 `index.html` 或给出对应的线上链接。报告页面是否已打开，以工具实际结果为准。

## 运行本机只读审计

本地页面的按钮盘点用户级配置和会话留存，使用同一个 [audit_context.py](../../../audit_context.py)。用户明确请 Codex 检查一个具体项目时，先确认 Claude 实际工作目录，再用下面的命令检查。用户只选其中一个范围时，按手帖核对该条目。

```bash
python3 -B "/脚本的绝对路径/audit_context.py" --project "/Claude实际工作的项目目录"
```

`-B` 禁止写入 Python 字节码缓存，`--project` 指定被检查的项目。Windows PowerShell 使用 `py -3 -B` 指定 Python 3。全部检查保持只读，保留原文件、登录状态与会话。

汇总每项发现的来源、状态和下一步核对入口，避免回显文件正文、凭据或会话内容。静态配置只能说明某个来源存在或已声明，实际加载和连接以会话证据为准。公网出口和浏览器会话按手帖的对应页面核对。
