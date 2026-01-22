import json
import http.server
import socketserver
import webbrowser
import logging
import sys
import os
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Any

from core.utils.diff import DiffViewer
from core.config import AppConfig
from core.service import DotfilesService
from core.models import Package, FileState
from core.executor import Executor

logger = logging.getLogger(__name__)

class DotfilesHandler(http.server.SimpleHTTPRequestHandler):
    """处理 Dotfiles Web 请求的 HTTP 处理器。"""
    def __init__(self, *args, config: AppConfig = None, service: DotfilesService = None, **kwargs):
        self.config = config
        self.service = service
        # 设置静态文件服务目录
        static_dir = Path(__file__).parent / "static"
        super().__init__(*args, directory=str(static_dir), **kwargs)

    def log_message(self, format, *args):
        """屏蔽默认日志以保持 CLI 洁净。"""
        pass

    def do_GET(self):
        """处理 GET 请求。"""
        parsed = urlparse(self.path)
        if parsed.path == '/api/scan':
            self.handle_api_scan()
        elif parsed.path == '/api/config':
            self.handle_api_config()
        elif parsed.path == '/api/diff':
            query = parse_qs(parsed.query)
            source = query.get('source', [None])[0]
            target = query.get('target', [None])[0]
            self.handle_api_diff(source, target)
        else:
            super().do_GET()

    def do_POST(self):
        """处理 POST 请求。"""
        parsed = urlparse(self.path)
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = json.loads(body) if body else {}

        if parsed.path == '/api/deploy':
            self.handle_api_deploy(data)
        elif parsed.path == '/api/restore':
            self.handle_api_restore(data)
        elif parsed.path == '/api/sync':
            self.handle_api_sync()
        elif parsed.path == '/api/backup-config':
            self.handle_api_backup_config(data)
        else:
            self.send_error(404, "Not Found")

    def send_json(self, data: Any):
        """发送 JSON 响应。"""
        response = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def send_api_error(self, message: str, code=400):
        """发送 API 错误响应。"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({"status": "error", "message": message}).encode('utf-8')
        self.wfile.write(response)

    def handle_api_sync(self):
        """处理同步请求。"""
        logs = self.service.sync_remote()
        self.send_json({"status": "success", "logs": logs})

    def handle_api_config(self):
        """处理配置获取请求。"""
        data = {
            "dotfiles_dir": str(self.config.dotfiles_dir),
            "target_root": str(self.config.target_root)
        }
        self.send_json(data)

    def handle_api_scan(self):
        """处理扫描请求。"""
        packages = self.service.scan_packages()
        # 序列化包数据
        data = []
        for pkg in packages:
            files = []
            for f in pkg.files:
                files.append({
                    "source": str(f.source),
                    "target": str(f.target),
                    "state": f.state.value,
                    "rel_path": str(f.source.relative_to(pkg.root))
                })
            data.append({
                "name": pkg.name,
                "status": pkg.status,
                "is_installed": pkg.is_installed,
                "path": str(pkg.root),
                "files": files
            })
        self.send_json(data)

    def handle_api_diff(self, source: str, target: str):
        """处理 Diff 请求。"""
        if not source or not target:
            self.send_api_error("Missing source or target param")
            return
        
        diff = DiffViewer.get_diff(Path(source), Path(target))
        self.send_json({"diff": diff})

    def handle_api_deploy(self, data):
        """处理部署请求。"""
        pkg_name = data.get('package')
        dry_run = data.get('dry_run', True)
        strategy = data.get('strategy', 'skip')
        
        packages = self.service.scan_packages()
        pkg = next((p for p in packages if p.name == pkg_name), None)
        
        if not pkg:
            self.send_api_error("Package not found")
            return

        # 部署 = 链接
        plan = self.service.deploy(pkg, conflict_strategy=strategy)
        
        logs = []
        if not plan.is_empty():
            logs = Executor.run(plan, dry_run=dry_run)
            
        self.send_json({"status": "success", "logs": logs, "dry_run": dry_run})

    def handle_api_restore(self, data):
        """处理恢复请求。"""
        pkg_name = data.get('package')
        dry_run = data.get('dry_run', True)
        # restore_strategy is ignored as restore now means UNLINK/UNDO
        
        packages = self.service.scan_packages()
        pkg = next((p for p in packages if p.name == pkg_name), None)
        
        if not pkg:
            self.send_api_error("Package not found")
            return

        # 恢复 = 取消链接 / 撤销
        plan = self.service.restore(pkg)
        
        logs = []
        if not plan.is_empty():
            logs = Executor.run(plan, dry_run=dry_run)
            
        self.send_json({"status": "success", "logs": logs, "dry_run": dry_run})

    def handle_api_backup_config(self, data):
        """处理备份 ~/.config 请求。"""
        dry_run = data.get('dry_run', True)

        plan, backup_path = self.service.backup_config_dir()
        logs = []
        if plan.is_empty():
            logs.append(".config not found or nothing to backup. / 未找到 .config 或无可备份内容。")
        else:
            logs = Executor.run(plan, dry_run=dry_run)
            if not dry_run and backup_path:
                logs.append(f"Backup created at: {backup_path} / 备份位置: {backup_path}")

        self.send_json({
            "status": "success",
            "logs": logs,
            "dry_run": dry_run,
            "backup_path": str(backup_path) if backup_path else None
        })

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_server(config: AppConfig, service: DotfilesService, port=9012, open_browser=True):
    """启动 Web 服务器。"""
    # 自定义处理器工厂
    def handler_factory(*args, **kwargs):
        return DotfilesHandler(*args, config=config, service=service, **kwargs)

    with ReusableTCPServer(("", port), handler_factory) as httpd:
        url = f"http://localhost:{port}"
        print(f"Serving Web GUI at {url}")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
