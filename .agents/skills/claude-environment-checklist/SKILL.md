---
name: claude-environment-checklist
description: 使用本项目排查 Claude 环境时，先打开下载项目里的网页手帖，再按用户选定的条目做只读核对。适用于排查 Claude 的公网出口、配置、记忆、外接工具、会话或浏览器网站数据。
---

# Claude 使用环境检查手帖

## 打开网页

用户要求用本项目执行第 0 步，按 [README 的 Codex 执行顺序](../../../README.md#给-codex-的执行顺序)操作。使用完整仓库启动器打印的本机地址，打开浏览器并点击「开始只读检查」。网页数字出现后，按[逐条复核手册](references/review.md)顺序核对并分批回填。查完一批就提交到原页面，确认进度后再查下一批。用户只要求盘点时，以其指定范围为准。用户只想浏览时，打开 [index.html](../../../index.html) 或线上预览。提到具体条目时，在网页地址后附上对应标识。

- 一次盘点本机配置、记忆和外接工具 → [第 0 步 · 一键只读检查](https://huangserva.github.io/claude-environment-checklist/#quick-audit)。
- 网络线路和公网出口 → [Claude 公网出口](https://huangserva.github.io/claude-environment-checklist/#network-egress)。
- 用户身份、记忆、指令文件和外接工具 → [配置、记忆与身份来源](https://huangserva.github.io/claude-environment-checklist/#identity-context)。
- 浏览器登录数据 → [浏览器会话](https://huangserva.github.io/claude-environment-checklist/#browser-data)。

第 0 步需要浏览器能连到目标电脑上的启动器。遇到阻塞时，报告实际进度和已经取得的本机地址。在线手帖提供浏览预览。

## 运行本机只读审计

本地页面的按钮盘点用户级配置和会话留存，使用同一个 [audit_context.py](../../../audit_context.py)。用户明确请 Codex 检查一个具体项目时，先确认 Claude 实际工作目录，再用下面的命令检查。用户只选其中一个范围时，按手帖核对该条目。

```bash
python3 -B "/脚本的绝对路径/audit_context.py" --project "/Claude实际工作的项目目录"
```

`-B` 禁止写入 Python 字节码缓存，`--project` 指定被检查的项目。Windows PowerShell 使用 `py -3 -B` 指定 Python 3。全部检查保持只读，保留原文件、登录状态与会话。

从网页交付完整的复核数量和分类结果。每个标记项保留编号、来源、证据和结论。只有当前会话的直接证据能证实读取。无法核验时照实说明，所有检查和复核保留原文件与会话。用户另有清理请求时，先核验备份，另行确定范围和保留的旧会话。
