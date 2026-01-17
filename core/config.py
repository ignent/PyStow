from pathlib import Path
import os

class AppConfig:
    """应用程序配置类。"""
    def __init__(self, dotfiles_dir: str = "~/.dotfiles", target_root: str = None):
        """初始化配置。"""
        self.dotfiles_dir = Path(os.path.expanduser(dotfiles_dir))
        self.target_root = Path(os.path.expanduser(target_root)) if target_root else Path.home()

    def ensure_dirs(self):
        """确保必要的目录存在（dotfiles_dir 必须已存在）。"""
        if not self.dotfiles_dir.exists():
            # In a real scenario, we might want to warn or create it.
            # For now, we assume the user has a dotfiles repo.
            pass
