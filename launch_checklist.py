"""Serve the checklist locally and run the fixed read-only audit on demand."""

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import subprocess
import sys
from threading import Lock, Thread
import webbrowser

from full_audit import add_local_checks

ROOT = Path(__file__).resolve().parent
TOKEN_TAG = b'<meta name="local-audit-token" content="">'
CONTENT_POLICY = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
    "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


def run_audit():
    result = subprocess.run(
        [sys.executable, "-B", str(ROOT / "audit_context.py"),
         "--project", str(Path.home()), "--json"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        encoding="utf-8",
        timeout=60,
        check=True,
    )
    report = json.loads(result.stdout)
    if not isinstance(report, dict) or report.get("mode") != "read-only":
        raise ValueError("Unexpected audit output")
    return add_local_checks(report, Path.home())


class ChecklistServer(ThreadingHTTPServer):
    def __init__(self):
        self.token = secrets.token_urlsafe(32)
        page = (ROOT / "index.html").read_bytes()
        if page.count(TOKEN_TAG) != 1:
            raise ValueError("Missing local checklist entry")
        local_tag = f'<meta name="local-audit-token" content="{self.token}">'.encode()
        self.page = page.replace(TOKEN_TAG, local_tag)
        self.audit_lock = Lock()
        super().__init__(("127.0.0.1", 0), ChecklistHandler)
        self.host = f"127.0.0.1:{self.server_port}"
        self.origin = f"http://{self.host}"


class ChecklistHandler(BaseHTTPRequestHandler):
    def setup(self):
        self.request.settimeout(8)
        super().setup()

    def log_message(self, *_):
        pass

    def respond(self, status, body, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", CONTENT_POLICY)
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def json_response(self, status, payload):
        self.respond(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.headers.get("Host") == self.server.host and self.path == "/":
            self.respond(HTTPStatus.OK, self.server.page, "text/html; charset=utf-8")
            return
        self.json_response(HTTPStatus.NOT_FOUND, {})

    def do_POST(self):
        if self.path != "/audit":
            self.json_response(HTTPStatus.NOT_FOUND, {})
            return
        if (
            self.headers.get("Host") != self.server.host
            or self.headers.get("Origin") != self.server.origin
            or not secrets.compare_digest(
                self.headers.get("X-Checklist-Token", "").encode(), self.server.token.encode()
            )
            or self.headers.get("Content-Length", "0") != "0"
            or self.headers.get("Transfer-Encoding") is not None
        ):
            self.json_response(HTTPStatus.FORBIDDEN, {})
            return
        if not self.server.audit_lock.acquire(blocking=False):
            self.json_response(HTTPStatus.CONFLICT, {"error": "已有检查在运行，请稍等后重试。"})
            return
        try:
            report = run_audit()
        except subprocess.TimeoutExpired:
            self.json_response(HTTPStatus.GATEWAY_TIMEOUT, {"error": "检查超时，可以重试。"})
            return
        except (OSError, subprocess.CalledProcessError, ValueError):
            self.json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "检查无法完成，请核对本机配置目录的读取权限。"})
            return
        finally:
            self.server.audit_lock.release()
        self.json_response(HTTPStatus.OK, report)


def main():
    parser = argparse.ArgumentParser(description="打开本地只读检查手帖")
    parser.add_argument("--no-open", action="store_true", help="打印网页地址，由调用方打开浏览器")
    args = parser.parse_args()
    with ChecklistServer() as server:
        print(f"打开本地手帖 {server.origin}/", flush=True)
        print("关闭这个终端窗口即可退出手帖。", flush=True)
        if not args.no_open:
            Thread(target=webbrowser.open, args=(f"{server.origin}/",), daemon=True).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
