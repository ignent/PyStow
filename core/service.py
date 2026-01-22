import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import logging

from .config import AppConfig
from .models import Package, Dotfile, FileState
from .detector import StateDetector
from .operations import SymlinkOperation, RemoveOperation, BackupOperation, RestoreBackupOperation, CopyOperation
from .executor import OperationPlan

logger = logging.getLogger(__name__)

import subprocess

from .utils.diff import DiffViewer

class DotfilesService:
    """Dotfiles 核心服务类。"""
    def __init__(self, config: AppConfig):
        """初始化服务。"""
        self.config = config
        self.config.ensure_dirs()

    def get_diff(self, dotfile: Dotfile) -> List[str]:
        """
        获取 dotfile 源文件与目标文件的差异。
        """
        return DiffViewer.get_diff(dotfile.source, dotfile.target)

    def sync_remote(self) -> List[str]:
        """
        从远程仓库拉取变更。
        返回日志列表。
        """
        logs = []
        if not (self.config.dotfiles_dir / ".git").exists():
            return ["Dotfiles directory is not a git repo / Dotfiles 目录不是 git 仓库。"]
        
        try:
            # 简单的 git pull
            result = subprocess.run(
                ["git", "pull"], 
                cwd=self.config.dotfiles_dir, 
                capture_output=True, 
                text=True
            )
            if result.stdout:
                logs.append(result.stdout)
            if result.stderr:
                logs.append(result.stderr)
            
            if result.returncode == 0:
                 logs.append("Sync successful / 同步成功。")
            else:
                 logs.append("Sync failed / 同步失败。")
                 
        except Exception as e:
            logs.append(f"Sync error / 同步出错: {str(e)}")
            
        return logs

    def scan_packages(self) -> List[Package]:
        """扫描 dotfiles 目录下的包。"""
        packages = []
        if not self.config.dotfiles_dir.exists():
             logger.warning(f"Dotfiles directory {self.config.dotfiles_dir} does not exist.")
             return packages

        for item in self.config.dotfiles_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # 我们将任何非隐藏目录视为一个包
                package = self._scan_single_package(item)
                packages.append(package)
        return packages

    def _scan_single_package(self, package_root: Path) -> Package:
        """扫描单个包。"""
        files = []
        # 遍历包目录
        for root, dirs, filenames in os.walk(package_root):
            # stow 通常忽略 .git 等文件，我们保持简单，至少跳过 .git
            if '.git' in dirs:
                dirs.remove('.git')
            
            for filename in filenames:
                source_path = Path(root) / filename
                rel_path = source_path.relative_to(package_root)
                
                # 目标是相对于用户主目录（或配置的目标根目录）
                # 在典型的 stow 用法中，我们 stow 到 ~
                target_path = self.config.target_root / rel_path
                
                state = StateDetector.detect(source_path, target_path)
                
                dotfile = Dotfile(
                    source=source_path,
                    target=target_path,
                    state=state
                )
                files.append(dotfile)
        
        is_installed = shutil.which(package_root.name) is not None
        return Package(name=package_root.name, root=package_root, files=files, is_installed=is_installed)

    def deploy(self, package: Package, conflict_strategy: str = "backup") -> OperationPlan:
        """部署（链接）包。"""
        return self.sync(package, action="link", conflict_strategy=conflict_strategy)

    def restore(self, package: Package) -> OperationPlan:
        """恢复（撤销链接）包。"""
        return self.sync(package, action="unlink")

    def backup_config_dir(self) -> Tuple[OperationPlan, Optional[Path]]:
        """
        备份用户目录下的 .config 文件夹。

        返回 (操作计划, 备份路径)。如果 .config 不存在，操作计划为空且路径为 None。
        """
        plan = OperationPlan()

        source_config = self.config.target_root / ".config"
        if not source_config.exists():
            logger.warning(".config directory does not exist under target root %s", self.config.target_root)
            return plan, None

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_root = self.config.target_root / ".dotfiles_backup" / "config"
        backup_path = backup_root / f"config-{timestamp}"

        plan.add(CopyOperation(source_config, backup_path, preserve_symlinks=True))
        return plan, backup_path

    def sync(self, package: Package, action: str = "link", conflict_strategy: str = "backup") -> OperationPlan:
        """
        同步包（链接或取消链接）。
        action: 'link' (deploy) or 'unlink' (restore/unstow)
        conflict_strategy: 'backup', 'overwrite' (only for link)
        """
        plan = OperationPlan()
        
        for dotfile in package.files:
            # 计算备份路径
            try:
                rel_path = dotfile.source.relative_to(self.config.dotfiles_dir)
            except ValueError:
                # 鉴于扫描逻辑，这不应发生，但作为回退
                rel_path = Path(dotfile.source.name)
            
            backup_path = self.config.target_root / ".dotfiles_backup" / rel_path

            if action == "link":
                if dotfile.state == FileState.LINKED:
                    continue
                
                if dotfile.state == FileState.MISSING:
                    plan.add(SymlinkOperation(dotfile.source, dotfile.target))
                
                elif dotfile.state == FileState.ORPHAN:
                    # 损坏的链接，移除并重新链接
                    plan.add(RemoveOperation(dotfile.target))
                    plan.add(SymlinkOperation(dotfile.source, dotfile.target))
                
                elif dotfile.state == FileState.CONFLICT:
                    if conflict_strategy == "overwrite":
                        plan.add(RemoveOperation(dotfile.target))
                        plan.add(SymlinkOperation(dotfile.source, dotfile.target))
                    elif conflict_strategy == "backup":
                        plan.add(BackupOperation(dotfile.target, backup_path))
                        plan.add(SymlinkOperation(dotfile.source, dotfile.target))
            
            elif action == "unlink":
                if dotfile.state == FileState.LINKED or dotfile.state == FileState.ORPHAN:
                    plan.add(RemoveOperation(dotfile.target))
                    # 检查备份并恢复
                    if backup_path.exists():
                        plan.add(RestoreBackupOperation(dotfile.target, backup_path))
                    else:
                        # 无备份: 实体化源文件 (复制)
                        plan.add(CopyOperation(dotfile.source, dotfile.target))
        
        return plan
