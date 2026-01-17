from typing import List
import sys
from .base import UserInterface
from core.models import Package, FileState
from core.executor import OperationPlan

class ConsoleUI(UserInterface):
    """命令行用户界面。"""
    def show_packages(self, packages: List[Package]) -> None:
        """显示包列表。"""
        print(f"\n{'#':<3} {'Package / 包':<20} {'Status / 状态':<15} {'Files / 文件'}")
        print("-" * 80)
        for idx, pkg in enumerate(packages, 1):
            file_stats = {
                FileState.LINKED: 0,
                FileState.CONFLICT: 0,
                FileState.MISSING: 0,
                FileState.ORPHAN: 0
            }
            for f in pkg.files:
                file_stats[f.state] += 1
            
            details = ", ".join([f"{k.value}:{v}" for k, v in file_stats.items() if v > 0])
            print(f"{idx:<3} {pkg.name:<20} {pkg.status:<15} {details}")
        print("-" * 80)

    def show_plan(self, plan: OperationPlan) -> None:
        """显示操作计划。"""
        if plan.is_empty():
            print("No operations planned. / 无计划操作。")
            return

        print("\nProposed Plan / 提议计划:")
        for op in plan:
            print(f" - {op.dry_run()}")
        print("")

    def confirm(self, message: str) -> bool:
        """请求确认。"""
        try:
            res = input(f"{message} [y/N]: ").strip().lower()
            return res == 'y'
        except KeyboardInterrupt:
            return False

    def show_message(self, message: str) -> None:
        """显示普通消息。"""
        print(message)

    def show_error(self, message: str) -> None:
        """显示错误消息。"""
        print(f"ERROR / 错误: {message}", file=sys.stderr)

    def select_package(self, packages: List[Package]) -> Package | None:
        """选择包。"""
        if not packages:
            self.show_error("No packages available. / 无可用包。")
            return None

        while True:
            try:
                choice = input("Select package number (or 'q' to quit) / 选择包编号 (或 'q' 退出): ").strip()
                if choice.lower() == 'q':
                    return None
                
                idx = int(choice)
                if 1 <= idx <= len(packages):
                    return packages[idx-1]
                else:
                    print("Invalid selection. / 无效选择。")
            except ValueError:
                print("Please enter a number. / 请输入数字。")
            except KeyboardInterrupt:
                return None
