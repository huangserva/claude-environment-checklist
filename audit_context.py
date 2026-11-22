#!/usr/bin/env python3
"""Read-only inventory of local Claude instructions, memories and connectors."""

import sys

sys.dont_write_bytecode = True

import argparse
import json
import os
from pathlib import Path
import re
import stat

START = "启动候选"
CONDITIONAL = "按条件"
CONFIGURED = "已配置"
STORED = "仅留存"
UNKNOWN = "未核验"
MISSING = "未发现"
LIMIT = 4 * 1024 * 1024
TOTAL_LIMIT = 32 * 1024 * 1024
WALK_LIMIT = 3000
INSTRUCTION_NAMES = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md")
SKIP_DIRS = {".git", ".claude", "node_modules", ".venv", "venv", "__pycache__", "vendor"}
TEXT_SUFFIXES = {".md", ".markdown", ".mdx", ".txt"}
MAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", re.I)
SECRET = re.compile(r"(?:sk-[\w-]{12,}|gh[pousr]_[\w]{12,}|eyJ[\w-]{16,}\.[\w.-]+)")
UNPRINTABLE = re.compile(r"[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]")
IDENTITY_LABEL = re.compile(
    r"^\s*(?:[-*]\s*)?(?:name|full name|user ?name|identity|email|"
    r"姓名|名字|用户名|邮箱|身份|别名)\s*[:：]", re.I | re.M
)
USER_NOTE = re.compile(r"^\s*(?:type|category):\s*['\"]?user\b", re.I | re.M)
FRONT_MATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)^---[ \t]*(?:\r?\n|\Z)", re.M | re.S)
PATH_RULE = re.compile(r"^paths\s*:", re.M)
IMPORT = re.compile(r"(?<![\w@])@((?:\\[ \t]|[^\s<>\"'|\[\](),;，；。])+)")
FENCE = re.compile(r"^\s*(?:\x60{3,}|~{3,})")
PROVIDER_FIELDS = (
    "ANTHROPIC_BASE_URL", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_BEDROCK_BASE_URL", "ANTHROPIC_VERTEX_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_USE_ANTHROPIC_AWS", "CLAUDE_CODE_USE_ANTHROPIC_GOOGLE_CLOUD", "CLAUDE_CODE_USE_MANTLE",
    "CLAUDE_CODE_PROVIDER_MANAGED_BY_HOST",
)


def inside(path, root):
    return path == root or root in path.parents


def safe_label(value):
    value = UNPRINTABLE.sub("·", str(value))
    return SECRET.sub("<凭据已省略>", MAIL.sub("<邮箱已省略>", value))


def object_value(value):
    return value if isinstance(value, dict) else {}


def visible_lines(text):
    fenced = False
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced:
            yield line


def absolute(value):
    return Path(value).expanduser().resolve()


def matches_project(value, locations):
    try:
        path = Path(value)
        return path.is_absolute() and path.resolve() in locations
    except (OSError, RuntimeError, ValueError):
        return False


def system_paths(home):
    if sys.platform == "darwin":
        managed = Path("/Library/Application Support/ClaudeCode")
        desktop = home / "Library/Application Support/Claude/claude_desktop_config.json"
    elif os.name == "nt":
        managed = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "ClaudeCode"
        app_data = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
        desktop = app_data / "Claude/claude_desktop_config.json"
    else:
        managed = Path("/etc/claude-code")
        desktop = None
    return managed.resolve(), desktop


class Audit:
    def __init__(self, home, work, project, config, managed, extra_files, backup_dirs):
        self.aliases = ((config, "<Claude配置>"), (work, "<工作目录>"), (project, "<项目目录>"),
                        (home, "~"), (managed, "<组织配置>"))
        self.allowed = tuple(root for root in (home, work, project, config, managed, *backup_dirs)
                             if root != Path(root.anchor))
        self.extra_files = set(extra_files)
        self.remaining = TOTAL_LIMIT
        self.rows = []
        self.external_directories = {}
        self.read_cache = {}
        self.documents = set()
        self.enabled_plugins = set()
        self.memory_directories = set()

    def path_label(self, path):
        for root, label in self.aliases:
            if path == root:
                return label
            if inside(path, root):
                return safe_label(label + "/" + path.relative_to(root).as_posix())
        directory = Path(os.path.abspath(path.parent))
        number = self.external_directories.setdefault(directory, len(self.external_directories) + 1)
        return safe_label(f"<外部目录 {number}>/" + path.name)

    def add(self, category, source, state, detail):
        row = {
            "category": category,
            "source": self.path_label(source) if isinstance(source, Path) else safe_label(source),
            "status": state,
            "detail": safe_label(detail),
        }
        if row not in self.rows:
            self.rows.append(row)

    def resolve(self, path):
        target = path.resolve(strict=True)
        if target not in self.extra_files and not any(inside(target, root) for root in self.allowed):
            raise PermissionError("目标位于核对范围之外")
        return target

    def read(self, path, category, markdown=False, required=False):
        key = (path, markdown)
        if key in self.read_cache:
            return self.read_cache[key]
        value = None
        try:
            target = self.resolve(path)
            info = target.stat()
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("非普通文件")
            if markdown and target.suffix.lower() not in TEXT_SUFFIXES:
                raise ValueError("引用目标不是可审阅的文本文档")
            if info.st_size > LIMIT:
                raise ValueError("超出单文件读取上限")
            if info.st_size > self.remaining or not self.remaining:
                self.add(category, path, UNKNOWN, "达到总读取上限")
                return None
            # O_NONBLOCK avoids waiting on a special file swapped in after the stat.
            read_flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
            with os.fdopen(os.open(target, read_flags), "rb") as fd:
                if not stat.S_ISREG(os.fstat(fd.fileno()).st_mode):
                    raise ValueError("非普通文件")
                contents = fd.read(min(LIMIT, self.remaining) + 1)
            if len(contents) > self.remaining:
                self.remaining = 0
                self.add(category, path, UNKNOWN, "达到总读取上限")
                return None
            self.remaining -= len(contents)
            if len(contents) > LIMIT:
                raise ValueError("超出单文件读取上限")
            value = (target, contents.decode("utf-8-sig"))
        except FileNotFoundError:
            if required:
                self.add(category, path, MISSING, "在该位置未找到文件")
        except UnicodeError:
            self.add(category, path, UNKNOWN, "文本编码无法核对")
        except (OSError, RuntimeError, ValueError):
            self.add(category, path, UNKNOWN, "无法读取、超出范围或文件类型不适用")
        self.read_cache[key] = value
        return value

    def entries(self, folder, category):
        try:
            target = self.resolve(folder)
            if not target.is_dir():
                self.add(category, folder, UNKNOWN, "预期目录无法核对")
                return []
            return sorted(folder.iterdir(), key=lambda item: item.name.casefold())
        except FileNotFoundError:
            return []
        except (OSError, RuntimeError):
            self.add(category, folder, UNKNOWN, "目录不可访问或超出范围")
            return []

    def walk(self, root, category, follow_links=False):
        directories = [root]
        visited = set()
        while directories:
            current = directories.pop()
            try:
                resolved = self.resolve(current)
            except FileNotFoundError:
                continue
            except (OSError, RuntimeError):
                self.add(category, current, UNKNOWN, "目录不可访问或超出范围")
                continue
            if resolved in visited:
                continue
            if len(visited) >= WALK_LIMIT:
                self.add(category, root, UNKNOWN, "达到目录遍历上限，下面的目录未核对")
                return
            visited.add(resolved)
            for path in self.entries(current, category):
                yield path
                try:
                    mode = path.lstat().st_mode
                    if path.name not in SKIP_DIRS and (stat.S_ISDIR(mode) or (
                            follow_links and stat.S_ISLNK(mode) and path.is_dir())):
                        directories.append(path)
                except OSError:
                    self.add(category, path, UNKNOWN, "无法检查文件类型")

    def document(self, path, category, status, note="", imports=False, depth=0):
        item = self.read(path, category, markdown=True, required=depth > 0)
        if item is None:
            return
        target, text = item
        key = (target, category, status)
        if key in self.documents:
            return
        self.documents.add(key)

        metadata = FRONT_MATTER.match(text)
        header, body = (metadata.group(1), text[metadata.end():]) if metadata else ("", text)
        plain_body = "\n".join(visible_lines(body))
        if PATH_RULE.search(header) and category == "规则":
            status = CONDITIONAL
        tags = []
        if MAIL.search(text):
            tags.append("含邮箱格式")
        if IDENTITY_LABEL.search(plain_body):
            tags.append("含身份类标签")
        if category == "自动记忆" and USER_NOTE.search(header):
            tags.append("含用户记忆类型标记")
        if target != Path(os.path.abspath(path)):
            tags.append("经符号链接")
        flags = "、".join(tags) if tags else "未命中内置身份线索"
        self.add(category, path, status, "；".join(filter(None, (note, flags))))
        if not imports:
            return

        for line in plain_body.splitlines():
            for raw in dict.fromkeys(IMPORT.findall(line)):
                name = raw.replace(r"\ ", " ").rstrip(":：")
                imported = Path(name).expanduser()
                if not imported.is_absolute():
                    imported = target.parent / imported
                if depth >= 4:
                    self.add("引用文件", imported, UNKNOWN, "超过四级引用深度")
                elif imported.suffix.lower() not in TEXT_SUFFIXES:
                    self.add("引用文件", imported, UNKNOWN, "引用目标扩展名不在文本审阅范围")
                else:
                    self.document(imported, "引用文件", status, "由指令文档引用", True, depth + 1)

    def json_file(self, path, category, required=False):
        item = self.read(path, category, required=required)
        if item is None:
            return None
        try:
            data = json.loads(item[1])
            if not isinstance(data, dict):
                raise ValueError
        except (ValueError, RecursionError):
            self.add(category, path, UNKNOWN, "无法解析为配置对象")
            return None
        return data

    def tools(self, path, data, scope, status=CONFIGURED):
        servers = object_value(data.get("mcpServers"))
        for i, name in enumerate(servers, 1):
            name = str(name)
            label = name if re.fullmatch(r"[\w-]{1,64}", name) else f"第 {i} 项"
            self.add("外接工具", path, status, f"{scope} · {label} · 连接与调用情况未核验")

    def profile(self, path, status, active_paths=(), required=False):
        data = self.json_file(path, "全局状态", required)
        if data is None:
            return
        keys = [k for k in ("oauthAccount", "userID", "machineID", "accountUuid", "organizationUuid") if k in data]
        projects = object_value(data.get("projects"))
        first_prompts = sum(bool(object_value(entry).get("firstPrompt")) for entry in projects.values())
        self.add("全局状态", path, status,
                 f"身份字段：{'、'.join(keys) or '未发现已知字段'}；含首条提示词的项目：{first_prompts}")
        tool_status = STORED if status == STORED else CONFIGURED
        self.tools(path, data, "用户级", tool_status)
        for i, (name, entry) in enumerate(projects.items(), 1):
            if status == CONFIGURED and matches_project(name, active_paths):
                scope = "当前项目级记录"
                project_status = tool_status
            else:
                scope = f"项目级记录 {i}（归属待核对）"
                project_status = STORED
            self.tools(path, object_value(entry), scope, project_status)

    def provider(self, source, environment, status, has_helper=False):
        keys = [key for key in PROVIDER_FIELDS if key in environment]
        if has_helper:
            keys.append("apiKeyHelper")
        if keys:
            self.add("服务端点与认证配置", source, status,
                     f"存在字段：{'、'.join(keys)}；值及实际采用情况未核验")

    def settings(self, path, scope, status=CONFIGURED):
        data = self.json_file(path, "设置")
        if data is None:
            return
        observed = [k for k in ("env", "hooks", "autoMemoryEnabled", "autoMemoryDirectory",
                                "claudeMdExcludes", "enabledPlugins") if k in data]
        self.add("设置", path, status, f"{scope}；相关字段：{'、'.join(observed) or '未见已知字段'}")
        self.provider(path, object_value(data.get("env")), status, "apiKeyHelper" in data)
        if status == STORED:
            return
        hooks = object_value(data.get("hooks"))
        for event in ("SessionStart", "UserPromptSubmit"):
            if event in hooks:
                self.add("钩子", path, CONFIGURED, f"{scope} · {event} · 脚本及返回内容未执行")
        self.enabled_plugins.update(k for k, v in object_value(data.get("enabledPlugins")).items() if v is True)
        memory = data.get("autoMemoryDirectory")
        if isinstance(memory, str) and memory and (Path(memory).is_absolute() or memory.startswith("~/")):
            try:
                self.memory_directories.add(absolute(memory))
            except (OSError, RuntimeError, ValueError):
                self.add("自动记忆", path, UNKNOWN, "配置指定的记忆路径无法核对")

    def extensions(self, root, scope):
        for folder, label in (("skills", "技能"), ("agents", "子代理"),
                              ("commands", "命令"), ("output-styles", "输出风格")):
            for path in self.walk(root / folder, label, follow_links=True):
                if (folder == "skills" and path.name == "SKILL.md") or (
                        folder != "skills" and path.suffix.lower() in TEXT_SUFFIXES):
                    self.document(path, label, CONDITIONAL, scope)

    def plugins(self, config):
        registry = config / "plugins/installed_plugins.json"
        data = self.json_file(registry, "插件")
        if data is None and self.enabled_plugins:
            self.add("插件", registry, UNKNOWN, "发现启用设置，未核对安装位置")
            return
        for index, name in enumerate(sorted(self.enabled_plugins), 1):
            records = object_value(data.get("plugins")).get(name)
            self.add("插件", registry, CONFIGURED, f"启用设置记录 {index}，实际加载范围待核验")
            for record in records if isinstance(records, list) else []:
                folder = object_value(record).get("installPath")
                if not isinstance(folder, str) or not Path(folder).is_absolute():
                    continue
                try:
                    root = absolute(folder)
                except (OSError, RuntimeError, ValueError):
                    self.add("插件", registry, UNKNOWN, "无法核对插件路径")
                    continue
                self.extensions(root, "插件")
                for path in (root / ".mcp.json", root / ".claude-plugin/plugin.json"):
                    entry = self.json_file(path, "插件")
                    if entry is not None:
                        self.tools(path, entry, "插件")
                        if "hooks" in entry or isinstance(entry.get("mcpServers"), (str, list)):
                            self.add("插件", path, CONFIGURED, "外部钩子或工具清单需要另核对")
                if (root / "hooks/hooks.json").is_file():
                    self.add("钩子", root / "hooks/hooks.json", CONFIGURED, "插件钩子清单")

    def inventory(self, home, work, project, config, managed, desktop, args):
        ancestors = (work, *work.parents)
        for folder in (managed, config, *ancestors):
            for name in INSTRUCTION_NAMES:
                state = CONDITIONAL if name == "AGENTS.md" else START
                self.document(folder / name, "指令", state, imports=True)
                if folder in ancestors and name != "CLAUDE.local.md":
                    self.document(folder / ".claude" / name, "指令", state, imports=True)

        if work != Path(work.anchor) and work != home:
            for path in self.walk(work, "项目指令"):
                if path.parent == work:
                    continue
                if path.name in INSTRUCTION_NAMES:
                    self.document(path, "指令", CONDITIONAL, "子目录指令", True)
                if path.name == ".claude":
                    for name in ("CLAUDE.md", "AGENTS.md"):
                        self.document(path / name, "指令", CONDITIONAL, "子目录指令", True)
                    for rule in self.walk(path / "rules", "规则", follow_links=True):
                        if rule.suffix == ".md":
                            self.document(rule, "规则", CONDITIONAL, "子目录规则", True)
        else:
            self.add("项目指令", work, UNKNOWN, "该位置是主目录或文件系统根；请用 --project 指定实际项目")

        for root in dict.fromkeys((config, managed, project / ".claude", work / ".claude")):
            for path in self.walk(root / "rules", "规则", follow_links=True):
                if path.suffix == ".md":
                    self.document(path, "规则", START, imports=True)
            self.extensions(root, "用户、组织或项目")

        settings_sources = [
            ("用户级", config / "settings.json"),
            ("项目级", project / ".claude/settings.json"),
            ("项目本地", project / ".claude/settings.local.json"),
            ("组织管理", managed / "managed-settings.json"),
        ]
        if work != project:
            settings_sources.extend((
                ("工作目录候选", work / ".claude/settings.json"),
                ("工作目录本地候选", work / ".claude/settings.local.json"),
            ))
        for scope, path in settings_sources:
            self.settings(path, scope)
        for path in self.entries(managed / "managed-settings.d", "设置"):
            if path.suffix == ".json":
                self.settings(path, "组织管理片段")
        for path in args.settings:
            self.settings(path, "手工指定的启动设置")
        self.plugins(config)

        default_profile = home / ".claude.json"
        active_paths = (project, work)
        if args.config_dir or os.environ.get("CLAUDE_CONFIG_DIR"):
            self.profile(config / ".claude.json", CONFIGURED, active_paths, required=True)
            self.profile(default_profile, UNKNOWN)
        else:
            self.profile(default_profile, CONFIGURED, active_paths, required=True)
        self.profile(home / ".claude.json.backup", STORED)
        if config != home / ".claude":
            self.profile(config / ".claude.json.backup", STORED)
        for folder in (config / "backups", *args.backup_dir):
            for path in self.entries(folder, "配置备份"):
                if path.name.startswith(".claude.json") or path.name in ("claude.json", "claude-code-profile.json"):
                    self.profile(path, STORED)
        for folder in args.backup_dir:
            for root in (folder, folder / "dot-claude", folder / "claude-code"):
                for name in ("settings.json", "settings.local.json", "settings.json.bak"):
                    self.settings(root / name, "历史设置副本", STORED)

        sources = [(project / ".mcp.json", "项目级"), (managed / "managed-mcp.json", "组织管理")]
        if desktop is not None:
            sources.append((desktop, "桌面端"))
        sources.extend((path, "手工指定的外部工具配置") for path in args.mcp_config)
        for path, scope in sources:
            data = self.json_file(path, "外接工具", required=True)
            if data is not None:
                self.add("外接工具", path, CONFIGURED, f"{scope} · 发现配置文件")
                self.tools(path, data, scope)

        for folder in self.entries(config / "projects", "项目存储"):
            if folder.is_symlink():
                self.add("项目存储", folder, UNKNOWN, "项目目录为符号链接，需单独确认")
                continue
            if not folder.is_dir():
                continue
            self.memory(folder / "memory", "已发现项目记忆位置，当前会话对应项目待核对")
            count = sum(path.suffix == ".jsonl" and path.is_file()
                        for path in self.entries(folder, "项目存储"))
            if count:
                self.add("本地会话", folder, STORED, f"{count} 份顶层会话记录，正文及恢复状态未核验")
        for folder in sorted(self.memory_directories):
            self.memory(folder, "设置里指定的记忆位置，当前会话是否采用待核对")
        if (config / "history.jsonl").is_file():
            self.add("本地历史", config / "history.jsonl", STORED, "发现本地历史，正文未读取")
        if (config / ".credentials.json").is_file():
            self.add("登录凭据", config / ".credentials.json", STORED, "凭据文件存在，正文未读取")
        self.provider("当前检测终端的环境", os.environ, UNKNOWN)

        self.add("实际会话", "已有 Claude Code 会话", UNKNOWN,
                 "对照 /status、/context all、/memory 和 /mcp，确认载入、连接与调用状态")
        self.add("启动参数与环境", "实际启动器、编辑器、组织策略或远程环境", UNKNOWN,
                 "手工核对自定义提示词、附加目录、恢复会话及未提供的启动配置")
        self.add("账号个性化", "Claude 网页或桌面端账号", UNKNOWN,
                 "从账号设置核对个人指令、云端记忆、项目知识及连接器")

    def memory(self, folder, note):
        for path in self.entries(folder, "自动记忆"):
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            kind = "自动记忆索引" if path.name == "MEMORY.md" else "按需记忆主题"
            self.document(path, "自动记忆", CONDITIONAL, f"{kind}；{note}")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Claude 配置、记忆和身份来源只读检查")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Claude 实际工作的目录")
    parser.add_argument("--config-dir", type=Path, help="Claude 实际使用的配置目录")
    parser.add_argument("--settings", type=Path, action="append", default=[], help="补查启动设置文件，可重复")
    parser.add_argument("--mcp-config", type=Path, action="append", default=[], help="补查外接工具配置，可重复")
    parser.add_argument("--backup-dir", type=Path, action="append", default=[], help="补查历史配置目录，可重复")
    parser.add_argument("--json", action="store_true", help="将结构化结果输出到终端")
    args = parser.parse_args()
    try:
        home = absolute(Path.home())
        work = absolute(args.project)
        if not work.is_dir():
            raise ValueError("工作目录不存在或不可访问")
        config = absolute(args.config_dir or os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude")
        managed, desktop = system_paths(home)
        project = next((parent for parent in (work, *work.parents) if (parent / ".git").exists()), work)
        for key in ("settings", "mcp_config", "backup_dir"):
            setattr(args, key, [absolute(path) for path in getattr(args, key)])
        extra = args.settings + args.mcp_config
        for folder in work.parents:
            extra.extend(folder / filename for filename in INSTRUCTION_NAMES)
            extra.extend((folder / ".claude/CLAUDE.md", folder / ".claude/AGENTS.md"))
        if desktop is not None:
            extra.append(desktop.resolve())
        audit = Audit(home, work, project, config, managed, extra, args.backup_dir)
        audit.inventory(home, work, project, config, managed, desktop, args)
    except (OSError, RuntimeError, ValueError):
        print("检测无法完成：工作目录或配置路径不可访问。", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({"mode": "read-only", "results": audit.rows}, ensure_ascii=False, indent=2))
    else:
        print("Claude 配置、记忆和身份来源 · 只读检测")
        print("静态文件结论以候选、可配置或留存标注。实际加载、连接和访问以会话证据为准。")
        for row in audit.rows:
            print(f"【{row['status']}】{row['category']} · {row['source']}")
            print(f"  {row['detail']}")
        print(f"共 {len(audit.rows)} 条。报告只显示位置、字段名和线索类型。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
