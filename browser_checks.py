"""Read-only Claude site metadata from known browser profile locations."""

import base64
from contextlib import closing
from hashlib import sha256
from itertools import islice
import os
from pathlib import Path
import re
import sqlite3
import stat
import struct
import sys
from time import monotonic
from urllib.parse import urlsplit


DOMAINS = ("claude.ai", "anthropic.com", "claude.com")
SAFARI_HOSTS = (*DOMAINS, "www.claude.ai", "www.anthropic.com", "console.anthropic.com",
                "platform.claude.com", "support.claude.com")
PROFILE_LIMIT = 32
CACHE_HEADER = struct.Struct("<QIIII")
CACHE_MAGIC = 0xFCFB6D1BA7725C30
CACHE_ENTRY = re.compile(r"[a-fA-F0-9]{16}_0")
PROFILE_NAME = re.compile(r"Default|Profile \d+|Guest Profile")


def target_domain(host):
    host = host.lower().strip(".")
    return next((domain for domain in DOMAINS if host == domain or host.endswith("." + domain)), None)


def children(folder, limit, want_dirs):
    """Return a bounded listing and whether the listing was incomplete."""
    try:
        with os.scandir(folder) as entries:
            sample = list(islice(entries, limit + 1))
            paths = [Path(entry.path) for entry in sample[:limit]
                     if (entry.is_dir if want_dirs else entry.is_file)(follow_symlinks=False)]
        return paths, len(sample) > limit
    except (FileNotFoundError, NotADirectoryError):
        return [], False
    except OSError:
        return [], True


def fingerprint(path):
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise OSError("Not a regular file")
        return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
    except FileNotFoundError:
        return None


def cookie_domains(path, firefox=False):
    """Query host columns only, without creating SQLite journals or locks."""
    table, column = ("moz_cookies", "host") if firefox else ("cookies", "host_key")
    files = (path, path.with_name(path.name + "-wal"), path.with_name(path.name + "-journal"))
    try:
        before = tuple(map(fingerprint, files))
        if before[0] is None:
            return set(), False
        if path.is_symlink() or any(info and info[2] for info in before[1:]):
            return set(), True
        where = f"{column} IN (?, ?) OR {column} LIKE ?"
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)) as db:
            deadline = monotonic() + .25
            db.set_progress_handler(lambda: int(monotonic() > deadline), 1000)
            domains = {domain for domain in DOMAINS
                       if db.execute(f"SELECT 1 FROM {table} WHERE {where} LIMIT 1",
                                     (domain, "." + domain, "%." + domain)).fetchone()}
        return (domains, False) if before == tuple(map(fingerprint, files)) else (set(), True)
    except (OSError, ValueError, sqlite3.Error):
        return set(), True


def cache_domains(folder, deadline):
    """Read Chromium Simple Cache keys, without reading response bodies."""
    paths, incomplete = children(folder, 3500, False)
    found = set()
    for path in paths:
        if monotonic() > deadline:
            return found, True
        if not CACHE_ENTRY.fullmatch(path.name):
            incomplete |= path.name == "data_0"
            continue
        try:
            with path.open("rb") as entry:
                magic, _, size, _, _ = CACHE_HEADER.unpack(entry.read(CACHE_HEADER.size))
                if magic != CACHE_MAGIC or not 0 < size <= 8192:
                    incomplete = True
                    continue
                key = entry.read(size)
            if len(key) != size:
                incomplete = True
                continue
            resource = key.decode("utf-8")
            if re.match(r"[01]/\d+/", resource):
                resource = resource.split("/", 2)[-1].rsplit(" ", 1)[-1]
            host = urlsplit(resource).hostname
            domain = target_domain(host) if host else None
            if domain:
                found.add(domain)
        except (OSError, ValueError, struct.error):
            incomplete = True
    return found, incomplete


def origin_names(folder, firefox=False):
    paths, incomplete = children(folder, 3000, True)
    pattern = r"https?\+\+\+([^+^]+)(?:[+^].*)?" if firefox else r"https?_([^_]+)_\d+\.indexeddb\.leveldb"
    matches = (re.fullmatch(pattern, path.name) for path in paths)
    return {domain for match in matches if match and (domain := target_domain(match[1]))}, incomplete


def chromium_roots(home):
    if sys.platform == "darwin":
        data, cache = home / "Library/Application Support", home / "Library/Caches"
        names = {
            "Chrome": ("Google/Chrome",), "Comet": ("Comet", "ai.perplexity.comet"),
            "Edge": ("Microsoft Edge",), "Brave": ("BraveSoftware/Brave-Browser",),
            "Chromium": ("Chromium",), "Vivaldi": ("Vivaldi",), "Arc": ("Arc/User Data",),
            "Dia": ("Dia/User Data",),
        }
    elif os.name == "nt":
        data = cache = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
        names = {
            "Chrome": ("Google/Chrome/User Data",), "Comet": ("Perplexity/Comet/User Data", "Comet/User Data"),
            "Edge": ("Microsoft/Edge/User Data",), "Brave": ("BraveSoftware/Brave-Browser/User Data",),
            "Chromium": ("Chromium/User Data",), "Vivaldi": ("Vivaldi/User Data",),
        }
    else:
        data = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        cache = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))
        names = {
            "Chrome": ("google-chrome", "google-chrome-beta"), "Comet": ("comet",),
            "Edge": ("microsoft-edge",), "Brave": ("BraveSoftware/Brave-Browser",),
            "Chromium": ("chromium",), "Vivaldi": ("vivaldi",),
        }
    return {browser: [(data / name, cache / name) for name in locations]
            for browser, locations in names.items()}


def row(browser, profile, kinds, incomplete):
    evidence = "；".join(f"{kind}：{'、'.join(sorted(domains))}" for kind, domains in kinds if domains)
    limitation = {"Safari": "专有网络缓存和 Cookie 需在 Safari 中核对",
                  "Firefox": "网络缓存需在 Firefox 中核对"}.get(browser)
    detail = evidence or "在可读取的站点索引中未发现匹配"
    if limitation:
        detail += "；" + limitation
    return {
        "browser": browser, "profile": profile,
        "status": "发现站点数据" if evidence else "未核验" if incomplete else "未发现匹配",
        "detail": detail, "incomplete": incomplete,
    }


def chromium_profiles(brand, locations, deadline):
    rows = []
    for data, cache in locations:
        candidates, incomplete = children(data, PROFILE_LIMIT * 4, True)
        profiles = []
        for path in candidates:
            try:
                if PROFILE_NAME.fullmatch(path.name) or fingerprint(path / "Preferences"):
                    profiles.append(path)
            except OSError:
                incomplete = True
        for profile in sorted(profiles)[:PROFILE_LIMIT]:
            if monotonic() > deadline:
                incomplete = True
                break
            label = profile.name if PROFILE_NAME.fullmatch(profile.name) else f"配置 {len(rows) + 1}"
            if any(item["profile"] == label for item in rows):
                label += f"（发现位置 {len(rows) + 1}）"
            cookies, cookie_limit = cookie_domains(profile / "Network/Cookies")
            legacy, legacy_limit = cookie_domains(profile / "Cookies")
            storage, storage_limit = origin_names(profile / "IndexedDB")
            caches = set()
            cache_limit = False
            for base in dict.fromkeys((profile, cache / profile.name)):
                for name in ("Cache/Cache_Data", "Cache"):
                    domains, partial = cache_domains(base / name, deadline)
                    caches.update(domains)
                    cache_limit |= partial
            rows.append(row(brand, label,
                            (("Cookie 域名", cookies | legacy), ("站点数据库", storage), ("网页缓存域名", caches)),
                            cookie_limit or legacy_limit or storage_limit or cache_limit))
        if incomplete or len(profiles) > PROFILE_LIMIT:
            rows.append({"browser": brand, "profile": "其他配置", "status": "未核验",
                         "detail": "默认目录不可访问或超过配置检查上限", "incomplete": True})
    return rows


def firefox_profiles(home):
    root = (home / "Library/Application Support/Firefox/Profiles" if sys.platform == "darwin"
            else Path(os.environ.get("APPDATA", home / "AppData/Roaming")) / "Mozilla/Firefox/Profiles"
            if os.name == "nt" else home / ".mozilla/firefox")
    profiles, incomplete = children(root, PROFILE_LIMIT, True)
    rows = []
    for index, profile in enumerate(sorted(profiles), 1):
        cookies, cookie_limit = cookie_domains(profile / "cookies.sqlite", firefox=True)
        storage, storage_limit = origin_names(profile / "storage/default", firefox=True)
        try:
            if cookies or cookie_limit or storage or storage_limit or fingerprint(profile / "prefs.js"):
                rows.append(row("Firefox", f"配置 {index}", (("Cookie 域名", cookies), ("站点存储", storage)), True))
        except OSError:
            incomplete = True
    if incomplete:
        rows.append({"browser": "Firefox", "profile": "其他配置", "status": "未核验",
                     "detail": "默认目录不可访问或超过配置检查上限", "incomplete": True})
    return rows


def safari_origins(folder, deadline):
    """Match WebKit's salted origin directory names for the known site hosts."""
    try:
        salt_path = folder / "salt"
        if not salt_path.is_file() or salt_path.is_symlink():
            return set()
        with salt_path.open("rb") as stream:
            salt = stream.read(65)
        if not 0 < len(salt) <= 64:
            return set()
        hashes = {}
        for host in SAFARI_HOSTS:
            for scheme in ("http", "https"):
                digest = sha256(f"{scheme}://{host}".encode() + salt).digest()
                hashes[base64.urlsafe_b64encode(digest).decode().rstrip("=")] = target_domain(host)
        partitions, _ = children(folder, 1500, True)
        found = set()
        for partition in partitions:
            if monotonic() > deadline:
                break
            for entry in (partition, *children(partition, 100, True)[0]):
                if entry.name in hashes and (entry / "origin").is_file():
                    found.add(hashes[entry.name])
        return found
    except OSError:
        return set()


def safari_profiles(home, deadline):
    lib = home / "Library"
    containers = (lib, lib / "Containers/com.apple.Safari/Data/Library")
    found, profiles = set(), []
    for base in containers:
        for root in (base / "WebKit/WebsiteData", base / "WebKit/com.apple.Safari/WebsiteData"):
            found |= safari_origins(root / "Default", deadline)
            for locations in ("Origins", "LocalStorage", "IndexedDB"):
                entries, _ = children(root / locations, 1500, locations != "LocalStorage")
                for entry in entries:
                    match = re.fullmatch(r"https?_([^_]+)_\d+(?:\.localstorage)?", entry.name)
                    if match and (domain := target_domain(match[1])):
                        found.add(domain)
        for store in (base / "WebKit/WebsiteDataStore", base / "WebKit/com.apple.Safari/WebsiteDataStore"):
            profiles.extend(children(store, PROFILE_LIMIT, True)[0])
    rows = [row("Safari", "默认网站数据位置", (("WebKit 站点存储", found),), True)]
    for index, profile in enumerate(sorted(set(profiles))[:PROFILE_LIMIT], 1):
        matches = safari_origins(profile / "Origins", deadline)
        rows.append(row("Safari", f"用户场景 {index}", (("WebKit 站点存储", matches),), True))
    return rows


def inspect_browsers(home):
    deadline = monotonic() + 10
    rows = safari_profiles(home, deadline) if sys.platform == "darwin" else []
    candidates = chromium_roots(home)
    for brand in ("Chrome", "Comet", "Edge", "Brave", "Chromium", "Vivaldi", "Arc", "Dia"):
        profiles = chromium_profiles(brand, candidates.get(brand, []), deadline)
        if profiles:
            rows.extend(profiles)
        elif brand in {"Chrome", "Comet", "Edge", "Brave"}:
            rows.append({"browser": brand, "profile": "已知默认目录", "status": "未发现默认配置",
                         "detail": "自定义配置路径请在浏览器中核对", "incomplete": False})
    rows.extend(firefox_profiles(home) or [{"browser": "Firefox", "profile": "已知默认目录",
                "status": "未发现默认配置", "detail": "自定义配置路径请在浏览器中核对", "incomplete": False}])
    return rows
