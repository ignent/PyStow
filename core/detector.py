from pathlib import Path
import os
from .models import FileState

class StateDetector:
    """文件状态检测器。"""
    @staticmethod
    def detect(source: Path, target: Path) -> FileState:
        """
        检测目标相对于源 dotfile 的状态。
        """
        if not target.exists(follow_symlinks=False) and not target.is_symlink():
            return FileState.MISSING

        if target.is_symlink():
            if not target.exists():
                return FileState.ORPHAN

            try:
                link_target = os.readlink(target)
                abs_link_target = Path(link_target)
                if not abs_link_target.is_absolute():
                    abs_link_target = target.parent / link_target
                
                abs_link_target = abs_link_target.resolve()
                resolved_source = source.resolve()

                if abs_link_target == resolved_source:
                    return FileState.LINKED
                else:
                    # 是链接，但不是指向我们的文件 -> 冲突
                    # 为了安全，任何不是我们的预存链接都视为冲突。
                    return FileState.CONFLICT
            except OSError:
                # 损坏的链接
                return FileState.ORPHAN
        
        # 存在且不是软链接 -> 冲突
        return FileState.CONFLICT
