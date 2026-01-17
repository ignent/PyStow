from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

class FileState(Enum):
    """文件状态枚举。"""
    LINKED = "linked"       # 正确链接
    CONFLICT = "conflict"   # 存在但不是正确的链接
    MISSING = "missing"     # 目标不存在
    ORPHAN = "orphan"       # 目标是损坏的链接或指向错误的源

@dataclass
class Dotfile:
    """单个 Dotfile 配置项。"""
    source: Path           # ~/.dotfiles/package/... 中的文件
    target: Path           # ~/... 中的目标路径
    state: FileState = FileState.MISSING

    @property
    def relative_source_path(self) -> Path:
        """返回相对于包根目录的路径。"""
        return self.source

@dataclass
class Package:
    """Dotfile 包模型。"""
    name: str
    root: Path             # ~/.dotfiles/<name>
    files: List[Dotfile] = field(default_factory=list)
    is_installed: bool = False

    @property
    def status(self) -> str:
        """获取包状态摘要。"""
        if not self.files:
            return "empty"
        # Simple summary logic
        return "present"
