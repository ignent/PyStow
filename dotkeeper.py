import argparse
import sys
import logging

from core.config import AppConfig
from core.service import DotfilesService
from core.executor import Executor
from gui.console import ConsoleUI

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def setup_parser() -> argparse.ArgumentParser:
    """设置并返回命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="DotKeeper - Dotfiles 管理工具")
    
    parser.add_argument("--dotfiles", default="~/.dotfiles", help="Dotfiles 目录路径")
    parser.add_argument("--target", default=None, help="目标根目录 (默认: 用户主目录)")
    parser.add_argument("--dry-run", action="store_true", help="仅显示计划不执行 (空跑)")
    parser.add_argument("--no-browser", action="store_true", help="Web 模式下不自动打开浏览器")
    parser.add_argument("--port", type=int, default=9012, help="Web 服务器端口")
    
    subparsers = parser.add_subparsers(dest="command", required=False)
    
    # 扫描命令
    subparsers.add_parser("scan", help="扫描包并显示状态")
    
    # 部署命令
    deploy_parser = subparsers.add_parser("deploy", help="部署包")
    deploy_parser.add_argument("package", help="包名")
    
    # 恢复命令
    restore_parser = subparsers.add_parser("restore", help="恢复包 (撤销)")
    restore_parser.add_argument("package", help="包名")

    # 备份 .config 命令
    subparsers.add_parser("backup-config", help="备份用户目录下的 .config 文件夹")
    
    # Web 服务命令
    subparsers.add_parser("web", help="启动 Web GUI")

    return parser

def main():
    """应用程序主入口点。"""
    parser = setup_parser()
    
    # argparse does not accept global options after subcommand (e.g. "backup-config --dry-run").
    # Normalize argv so global options can appear either before or after the subcommand.
    known_commands = {"scan", "deploy", "restore", "backup-config", "web"}
    global_opts = {
        "--dry-run": 0,
        "--no-browser": 0,
        "--dotfiles": 1,
        "--target": 1,
        "--port": 1,
    }

    argv = sys.argv[1:]
    cmd_idx = next((i for i, tok in enumerate(argv) if tok in known_commands), None)
    if cmd_idx is not None:
        before = argv[:cmd_idx]
        cmd = argv[cmd_idx]
        after = argv[cmd_idx + 1:]

        moved = []
        rest = []
        i = 0
        while i < len(after):
            tok = after[i]

            matched_opt = None
            matched_val = None
            for opt, arity in global_opts.items():
                if tok == opt:
                    matched_opt = opt
                    if arity == 1:
                        if i + 1 >= len(after):
                            matched_opt = None
                            break
                        matched_val = after[i + 1]
                    break
                if arity == 1 and tok.startswith(opt + "="):
                    matched_opt = opt
                    matched_val = tok.split("=", 1)[1]
                    break

            if matched_opt:
                if matched_opt not in before and matched_opt not in moved:
                    moved.append(matched_opt)
                    if matched_val is not None:
                        moved.append(matched_val)
                i += 1 + global_opts[matched_opt]
                continue

            rest.append(tok)
            i += 1

        argv = before + moved + [cmd] + rest

    args = parser.parse_args(argv)
    
    config = AppConfig(
        dotfiles_dir=args.dotfiles,
        target_root=args.target
    )
    
    service = DotfilesService(config)
    
    try:
        if args.command == "web" or args.command is None:
            from gui.web_server import run_server
            run_server(config, service, port=args.port, open_browser=not args.no_browser)
            return

        # 命令行模式
        ui = ConsoleUI()

        if args.command == "scan":
            packages = service.scan_packages()
            ui.show_packages(packages)
            
        elif args.command == "deploy":
            packages = service.scan_packages()
            pkg = next((p for p in packages if p.name == args.package), None)
            if not pkg:
                ui.show_error(f"Package '{args.package}' not found / 未找到包 '{args.package}'。")
                sys.exit(1)
            
            plan = service.deploy(pkg)
            ui.show_plan(plan)
            if not plan.is_empty():
                if args.dry_run:
                    ui.show_message("\nThis was a dry-run. Use without --dry-run to apply. / 这是一个空跑。使用无 --dry-run 参数来执行。")
                else:
                    Executor.run(plan, dry_run=False)
                    
        elif args.command == "restore":
            packages = service.scan_packages()
            pkg = next((p for p in packages if p.name == args.package), None)
            if not pkg:
                ui.show_error(f"Package '{args.package}' not found / 未找到包 '{args.package}'。")
                sys.exit(1)
            
            plan = service.restore(pkg)
            ui.show_plan(plan)
            if not plan.is_empty():
                if args.dry_run:
                    ui.show_message("\nThis was a dry-run. Use without --dry-run to apply. / 这是一个空跑。使用无 --dry-run 参数来执行。")
                else:
                    Executor.run(plan, dry_run=False)

        elif args.command == "backup-config":
            plan, backup_path = service.backup_config_dir()
            ui.show_plan(plan)
            if plan.is_empty():
                ui.show_message(".config not found or nothing to backup. / 未找到 .config 或无可备份内容。")
            else:
                if args.dry_run:
                    Executor.run(plan, dry_run=True)
                    ui.show_message("\nThis was a dry-run. Use without --dry-run to apply. / 这是一个空跑。使用无 --dry-run 参数来执行。")
                else:
                    Executor.run(plan, dry_run=False)
                    if backup_path:
                        ui.show_message(f"Backup created at: {backup_path} / 备份位置: {backup_path}")
                    
    except Exception as e:
        logger.exception("An error occurred / 发生错误")
        sys.exit(1)

if __name__ == "__main__":
    main()
