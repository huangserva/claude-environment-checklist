# Claude 使用环境检查手帖

[打开在线手帖](https://huangserva.github.io/claude-environment-checklist/) · [下载单文件检测脚本](https://huangserva.github.io/claude-environment-checklist/#identity-context)

手帖按项检查 Claude 的公网出口、配置与记忆、备份与会话归档、缓存与日志、桌面数据、命令行凭据和浏览器会话。每项有手动步骤，也可以展开「交给 Codex」复制对应的核对指令。

## 一条命令开始检测

只需安装 Python 3。把手帖第 2 项的 `audit_context.py` 保存到「下载」目录，从 Claude 实际工作的项目目录运行对应命令。脚本已内置原版 `claude-cleanup` 的只读审计。

**macOS 或 Linux**

```bash
python3 -B "$HOME/Downloads/audit_context.py"
```

**Windows PowerShell**

```powershell
py -3 -B "$HOME\Downloads\audit_context.py"
```

Windows 用 `-3` 选用 Python 3。两条命令都用 `-B` 禁止 Python 写入缓存。脚本在其他位置时，把命令中的文件路径换成实际路径。

## 检测结果怎么读

| 部分 | 检查内容 | 适用系统 |
| --- | --- | --- |
| 原版只读审计 | 盘点默认目录里的缓存、日志、桌面应用数据、相关进程数、遥测设置、精简模式和时区。 | macOS。其他系统标为「不适用」。 |
| 配置、记忆与工具 | 列出指令文档及引用、自动记忆、项目记录、历史配置、外接工具、插件、钩子和服务认证配置。 | macOS、Windows、Linux。 |

**脚本只读本机状态，结果仅输出到终端。** 它列出来源、状态和线索类型，凭据和文件正文保留在本机。看到「启动候选」或「已配置」时，可在实际会话中核对是否加载或连接。云端账号记忆在账号设置里另查。[Claude Code 指令与记忆说明](https://code.claude.com/docs/en/memory)

查公网出口和浏览器网站数据时，请按在线手帖操作。出口检测先核对检测站与 Claude 请求实际走的是同一条线路，再记录检测站回显的地址。

## 自定义目录

| 选项 | 用途 |
| --- | --- |
| `--project 路径` | 指定 Claude 实际工作的目录。 |
| `--config-dir 路径` | 指定配置检查使用的 Claude 目录。原版审计仍盘点 macOS 默认目录。 |
| `--settings 文件`、`--mcp-config 文件` | 补查自定义启动设置和外接工具配置。可以重复指定。 |
| `--backup-dir 目录` | 补查历史配置备份。可以重复指定。 |
| `--json` | 将两部分结果以便于程序读取的结构化格式输出到终端。 |

无法读取、超出核对范围或达到读取上限的项目标为「未核验」。

## 原版来源

脚本沿用 Suyuan 的 `claude-cleanup` 只读审计逻辑，并保留上游版权和许可。[原版源码](https://github.com/suyuan2022/suyuan-skill/blob/8babd4557a4774ca8e3d5b784d82f0ee5a4565e5/claude-cleanup/scripts/claude_cleanup.py) · [原版开源许可](https://github.com/suyuan2022/suyuan-skill/blob/8babd4557a4774ca8e3d5b784d82f0ee5a4565e5/LICENSE)
