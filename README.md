# Claude 使用环境检查手帖

一套用于 Claude 账号使用中断后的**本机只读排查与恢复手帖**。先查旧配置、记忆、外接工具和会话留存，再按证据决定哪些要保留、哪些要整理。账号停用原因和申诉结果以 Anthropic 的通知与支持回复为准。[Anthropic 账号申诉说明](https://support.claude.com/en/articles/8241253-safeguards-warnings-and-appeals)

## 让 Codex 帮你跑完第 0 步

在**要检查的那台电脑**打开 Codex，把下面这句话连同链接发给它。

> 请用这个项目在当前电脑做一次第 0 步只读检查。下载完整仓库，启动并打开它的本地网页，在网页上点「开始只读检查」。等页面出结果，汇报八项检查、建议复核的数字，以及浏览器有没有 Claude 相关网站数据。https://github.com/huangserva/claude-environment-checklist

### 给 Codex 的执行顺序

用户明确要求用本项目检查时，按下面的顺序走到网页显示结果为止。用户只说「查看仓库」时，可以介绍用途或打开预览，等用户明确要求开始检测。

1. **拿到完整项目。** 用终端克隆下方 GitHub 仓库。在目标电脑已经有此仓库时，确认来源和所需文件齐全后可复用。读取仓库里的 [Codex Skill](.agents/skills/claude-environment-checklist/SKILL.md)。
2. **启动本地手帖。** 保持启动器进程运行。在仓库目录执行 `python3 -B launch_checklist.py --no-open`，Windows 用 `py -3 -B launch_checklist.py --no-open`。参数 `--no-open` 让启动器只打印本机网页地址，再由 Codex 的浏览器工具打开。参数 `-B` 禁止写入 Python 字节码缓存，Windows 的 `-3` 指定 Python 3。
3. **打开网页，点击检查。** 使用浏览器工具打开启动器打印的本机地址，确认进入「第 0 步」，点击「开始只读检查」，等待页面显示「检查完成」及数字结果。用户已明确请求检测时，无需再让用户复制命令、点击按钮或另行输入项目路径。
4. **交付网页结果。** 保留结果页和启动器，汇报八项检查的概况、建议复核数、未核验数，以及哪些浏览器配置发现了相关网站数据。使用本项目时以网页结果为准。缺少本机访问或浏览器操作能力时，说明哪一步卡住并给出已经取得的地址或进度。用户授权的是只读检查，清理前需另行选定范围并核验备份。

## 下载项目，打开手帖

这一节适用于希望自己操作的用户。

**下载完整项目，双击启动文件，点「开始只读检查」。** 结果直接显示在手帖里。电脑需要 Python 3.9 或更新版本。

1. **下载项目。** 在终端运行下面这条克隆命令。已经克隆的用户可以先拉取最新版本。

   ```bash
   git clone https://github.com/huangserva/claude-environment-checklist.git
   ```

2. **启动本地手帖。** macOS 双击 `Start-Checklist.command`，Windows 双击 `Start-Checklist.cmd`。Linux 在项目文件夹运行 `python3 -B launch_checklist.py`，其中 `-B` 禁止写入 Python 字节码缓存。启动器会用浏览器打开手帖。
3. **点「开始只读检查」。** 第 0 步一次盘点八项。报告先给结论和数字，再列各项覆盖情况及逐浏览器、逐配置的结果。关闭启动器的终端窗口即可退出手帖。

[预览网页手帖](https://huangserva.github.io/claude-environment-checklist/)

[![本地手帖第 0 步的检查结果，使用测试数据展示建议复核、未核验和其他记录](assets/homepage.png)](https://huangserva.github.io/claude-environment-checklist/)

## 遇到什么问题，从哪一项查

| 遇到的问题 | 建议先看 |
| --- | --- |
| 想先了解本机现状，保留所有文件和设置 | [第 0 步 · 一键只读检查](https://huangserva.github.io/claude-environment-checklist/#quick-audit)。一次盘点配置、记忆、外接工具和本机会话记录。 |
| Claude 连不上，或者浏览器和终端的公网出口不同 | [公网出口](https://huangserva.github.io/claude-environment-checklist/#network-egress)。对照 Claude 的已有连接与出口检测请求，确认它们实际走的线路。 |
| Claude 知道你没在当前对话里提过的姓名、偏好或旧项目 | [配置、记忆与身份来源](https://huangserva.github.io/claude-environment-checklist/#identity-context)。从指令文件、自动记忆、项目记录、插件和外接工具找来源。 |
| 同一台电脑上的浏览器登录状态不同 | [浏览器会话](https://huangserva.github.io/claude-environment-checklist/#browser-data)。逐个浏览器配置查 Claude 和 Anthropic 的网站数据，另行核验当前登录状态。 |
| 换机、重装，或准备清理本机数据 | [完整备份](https://huangserva.github.io/claude-environment-checklist/#old-backup)和[会话归档](https://huangserva.github.io/claude-environment-checklist/#sessions)。先核对要保留的会话和可恢复的副本。 |

手帖也提供缓存与日志、桌面应用数据和命令行凭据的核对步骤。

## 怎么用

### 打开网页逐项核对

从手帖左侧可以按条目继续核验实际公网出口、浏览器登录是否有效、具体项目配置等。只想浏览时，可以直接打开 `index.html`。

### 用 Codex 或终端检查具体项目

可以在 Codex 中打开下载的项目，调用 `$claude-environment-checklist`。手帖各条目也提供「交给 Codex」的指令。[查看技能文件](.agents/skills/claude-environment-checklist/SKILL.md)

从终端执行时，在下载的 `claude-environment-checklist` 文件夹运行下面的命令。把示例路径换成 Claude 实际工作的项目目录。

**macOS 或 Linux**

```bash
python3 -B audit_context.py --project "/Claude实际工作的项目目录"
```

**Windows PowerShell**

```powershell
py -3 -B audit_context.py --project "C:\Claude实际工作的项目目录"
```

`-B` 禁止 Python 写入字节码缓存，`--project` 指定要检查的项目。Windows 的 `-3` 指定 Python 3。

在 macOS 上，脚本会同时输出原版 `claude-cleanup` 的本机审计和本项目的配置检查。前者盘点默认目录、缓存、日志、桌面数据和相关进程，后者查配置、记忆和外接工具。Windows 和 Linux 会运行配置检查，原版专用于 macOS 的审计标为「不适用」。

### 怎么判断结果

网页先给本次结论，并按三组显示数量。

- **建议复核**。包括本机身份线索、已声明的外接工具、会影响会话的自动启动项，以及发现 Claude 相关站点留存的浏览器配置。按类别查看数量与来源，核对是否符合预期。
- **未核验**。本机盘点未能确认的条目，例如具体项目的指令和当前会话读取了哪些内容。
- **其他记录**。配置、技能或会话等常规盘点明细。

浏览器检查针对 Claude 和 Anthropic 的域名。Chrome、Comet、Edge 等会查询可读的 Cookie 域名、站点数据库目录和支持的网页缓存索引。Safari 使用可读的 WebKit 站点存储，Firefox 检查 Cookie 域名与站点存储。报告会标出受权限、存储格式或正在写入影响的范围。[Chromium 缓存格式](https://chromium.googlesource.com/chromium/src/net/+/refs/heads/main/disk_cache/simple/simple_entry_format.h) · [WebKit 站点存储格式](https://github.com/WebKit/WebKit/blob/main/Source/WebCore/storage/StorageUtilities.cpp)

第 0 步保留离线只读行为。报告列出代理线索，Claude 的实际公网出口、登录有效性和备份能否恢复需要按条目核验。

### 复核、备份与清理

1. 先保留并校验一份独立的备份，确认要保留的旧会话都能读、都可以恢复。
2. 从报告列出的来源逐项复核。公网出口以 Claude 实际连接为准，浏览器与命令行的登录状态分别确认。
3. 单独选定需要清理的缓存、旧登录数据或配置。由用户确认范围后处理，保留已确认有用的配置和会话。
4. 按同一范围重跑只读检查，对照前后结果，再检查保留的会话和备份。账号仍停用时，通过官方支持核对状态。

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
