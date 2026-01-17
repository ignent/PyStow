import difflib
from pathlib import Path
from typing import List

class DiffViewer:
    """Diff 查看器工具。"""
    @staticmethod
    def get_diff(source: Path, target: Path) -> List[str]:
        """
        生成文件差异。
        返回 Diff 行列表。
        """
        if not source.exists() or not target.exists():
            return ["One of the files does not exist."]
        
        if source.is_dir() or target.is_dir():
            return ["Directory diff not supported yet."]
            
        try:
            with open(source, 'r', encoding='utf-8') as f:
                source_lines = f.readlines()
            with open(target, 'r', encoding='utf-8') as f:
                target_lines = f.readlines()
                
            diff = difflib.unified_diff(
                target_lines, 
                source_lines, 
                fromfile=str(target), 
                tofile=str(source),
                lineterm=''
            )
            return list(diff)
        except Exception as e:
            return [f"Error generating diff: {e}"]
