"""Combine the existing audit with the remaining local handbook checks."""

import os
from pathlib import Path
import sys
from uuid import uuid4

from browser_checks import children, inspect_browsers


def known_paths(paths):
    found = 0
    incomplete = False
    for path in paths:
        try:
            path.lstat()
            found += 1
        except FileNotFoundError:
            pass
        except OSError:
            incomplete = True
    return found, incomplete


def check(section, title, detail, status="已盘点"):
    return {"section": section, "title": title, "status": status, "detail": detail}


def add_local_checks(report, home):
    counts = report.get("inventory_counts", {})
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR") or home / ".claude").expanduser()
    backups, backup_limit = children(home / "ClaudeBackups", 200, True)
    credentials, credential_limit = known_paths((config / ".credentials.json", home / ".claude.json"))
    cleanup = report["cleanup_audit"]
    if cleanup.get("scope"):
        caches = len(cleanup["cache_log_candidates"])
        desktop = len(cleanup["desktop_data_candidates"])
        cache_limit = desktop_limit = cleanup["status"] != "已审计"
    else:
        caches, cache_limit = known_paths(config / name for name in ("cache", "logs", "debug", "telemetry"))
        if os.name == "nt":
            bases = (Path(os.environ.get("APPDATA", home / "AppData/Roaming")),
                     Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local")))
        else:
            bases = (Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")),)
        desktop, desktop_limit = known_paths(base / name for base in bases for name in ("Claude", "Claude-3p"))

    proxy_count = sum(bool(os.environ.get(name) or os.environ.get(name.lower()))
                      for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"))
    browsers = inspect_browsers(home)
    matches = [item for item in browsers if item["status"] == "发现站点数据"]
    limits = sum(item["incomplete"] for item in browsers)
    for item in matches:
        report["results"].append({
            "category": "浏览器站点留存", "source": f"{item['browser']} · {item['profile']}",
            "status": "仅留存", "detail": item["detail"], "review_kind": "browser",
        })
    report["scan_id"] = str(uuid4())
    marked = (row for row in report["results"] if row.get("identity_clue") or row.get("review_kind"))
    for number, row in enumerate(marked, 1):
        row["review_id"] = f"R{number:03d}"
    report["browsers"] = browsers
    report["coverage"] = [
        check("network-egress", "Claude 公网出口",
              f"当前终端发现 {proxy_count} 种代理环境设置。Claude 的实际公网地址需核对同一条连接线路。",
              "实际出口待核验"),
        check("identity-context", "配置、记忆与工具",
              "已盘点本机可访问的配置、指令、记忆、外接工具与钩子。当前会话实际载入情况需另核对。"),
        check("old-backup", "完整备份",
              f"找到 {len(backups)} 个默认备份目录、{counts.get('profiles_in_backup', 0)} 份全局配置副本。恢复能力待验证。",
              "部分未核验" if backup_limit else "已盘点"),
        check("sessions", "会话归档",
              f"找到 {counts.get('sessions', 0)} 份顶层 Claude Code 会话文件。归档副本及云端会话待核对。"),
        check("cache", "缓存和日志", f"找到 {caches} 个 Claude 缓存和日志位置。",
              "部分未核验" if cache_limit else "已盘点"),
        check("desktop", "桌面应用数据", f"找到 {desktop} 个 Claude 桌面数据候选位置。",
              "部分未核验" if desktop_limit else "已盘点"),
        check("credentials", "命令行登录凭据",
              f"发现 {credentials} 个配置或凭据文件位置。系统钥匙串与登录有效性待核对。",
              "部分未核验" if credential_limit else "已盘点"),
        check("browser-data", "浏览器站点数据与缓存",
              f"{len(matches)} 个配置发现 Claude 相关站点数据，{limits} 个配置有未核验的存储项目。登录有效性需在浏览器内核对。",
              "部分未核验" if limits else "已盘点"),
    ]
    return report
