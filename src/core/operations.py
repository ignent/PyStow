from abc import ABC, abstractmethod
from pathlib import Path
import shutil
import os
import logging

logger = logging.getLogger(__name__)

class Operation(ABC):
    """抽象操作基类。"""
    def __init__(self, description: str):
        self.description = description

    @abstractmethod
    def dry_run(self) -> str:
        """返回描述将发生情况的字符串。"""
        pass

    @abstractmethod
    def apply(self) -> None:
        """执行操作。"""
        pass

class BackupOperation(Operation):
    """备份操作。"""
    def __init__(self, target: Path, backup_path: Path):
        super().__init__(f"Backup {target} to {backup_path} / 备份 {target} 到 {backup_path}")
        self.target = target
        self.backup_path = backup_path

    def dry_run(self) -> str:
        return f"[BACKUP] Move '{self.target}' to '{self.backup_path}' / 移动 '{self.target}' 到 '{self.backup_path}'"

    def apply(self) -> None:
        if self.target.exists() or self.target.is_symlink():
            self.backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.backup_path.exists():
                # 轮转现有备份
                import time
                timestamp = int(time.time())
                archive_path = self.backup_path.with_name(f"{self.backup_path.name}.{timestamp}")
                shutil.move(self.backup_path, archive_path)
            
            shutil.move(self.target, self.backup_path)

class RestoreBackupOperation(Operation):
    """恢复备份操作。"""
    def __init__(self, target: Path, backup_path: Path):
        super().__init__(f"Restore {target} from {backup_path} / 从 {backup_path} 恢复 {target}")
        self.target = target
        self.backup_path = backup_path

    def dry_run(self) -> str:
        if self.backup_path.exists():
            return f"[RESTORE] Move '{self.backup_path}' to '{self.target}' / 移动 '{self.backup_path}' 到 '{self.target}'"
        return f"[RESTORE] No backup found at '{self.backup_path}' (Skipping) / 未在 '{self.backup_path}' 找到备份 (跳过)"

    def apply(self) -> None:
        if self.backup_path.exists():
            # 目标应该已经清除，但做安全检查
            if self.target.exists() or self.target.is_symlink():
                if self.target.is_dir() and not self.target.is_symlink():
                    shutil.rmtree(self.target)
                else:
                    os.unlink(self.target)
            
            self.target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(self.backup_path, self.target)
            
            # 清理空备份目录？可选。


class SymlinkOperation(Operation):
    """创建软链接操作。"""
    def __init__(self, src: Path, dst: Path):
        super().__init__(f"Link {dst} -> {src} / 链接 {dst} -> {src}")
        self.src = src
        self.dst = dst

    def dry_run(self) -> str:
        return f"[LINK] Create symlink '{self.dst}' -> '{self.src}' / 创建软链接 '{self.dst}' -> '{self.src}'"

    def apply(self) -> None:
        if self.dst.exists() or self.dst.is_symlink():
            if self.dst.is_symlink():
                 os.unlink(self.dst)
            else:
                 raise FileExistsError(f"Target {self.dst} still exists. Backup failed or not scheduled?")
        
        self.dst.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            target_dir = self.dst.parent
            rel_src = os.path.relpath(self.src, target_dir)
            os.symlink(rel_src, self.dst)
        except ValueError:
            # 如果路径在不同驱动器上或无法计算相对路径
            os.symlink(self.src, self.dst)

class CopyOperation(Operation):
    """复制/实体化操作。"""
    def __init__(self, src: Path, dst: Path):
        super().__init__(f"Materialize {src} to {dst} / 实体化 {src} 到 {dst}")
        self.src = src
        self.dst = dst

    def dry_run(self) -> str:
        return f"[COPY] Materialize '{self.src}' to '{self.dst}' / 实体化 '{self.src}' 到 '{self.dst}'"

    def apply(self) -> None:
        self.dst.parent.mkdir(parents=True, exist_ok=True)
        if self.src.is_dir():
            shutil.copytree(self.src, self.dst, dirs_exist_ok=True)
        else:
            shutil.copy2(self.src, self.dst)

class RemoveOperation(Operation):
    """删除/移除操作。"""
    def __init__(self, target: Path):
        super().__init__(f"Remove {target} / 删除 {target}")
        self.target = target

    def dry_run(self) -> str:
        return f"[REMOVE] Delete '{self.target}' / 删除 '{self.target}'"

    def apply(self) -> None:
        try:
            # 文件的内容
            if self.target.is_symlink():
                os.unlink(self.target)
            elif self.target.is_dir():
                shutil.rmtree(self.target)
            elif self.target.exists():
                os.unlink(self.target)
        except FileNotFoundError:
            pass # 已经不存在，这很好
