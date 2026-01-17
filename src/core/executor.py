from typing import List
from .operations import Operation
import logging

logger = logging.getLogger(__name__)

class OperationPlan:
    """操作计划。"""
    def __init__(self, operations: List[Operation] = None):
        """初始化操作计划。"""
        self.operations = operations or []

    def add(self, operation: Operation):
        """添加操作。"""
        self.operations.append(operation)

    def is_empty(self) -> bool:
        """检查计划是否为空。"""
        return len(self.operations) == 0

    def __iter__(self):
        return iter(self.operations)

class Executor:
    """操作执行器。"""
    @staticmethod
    def run(plan: OperationPlan, dry_run: bool = True) -> List[str]:
        """
        执行操作计划。
        返回执行日志列表。
        """
        logs = []
        for op in plan.operations:
            if dry_run:
                msg = f"[DRY-RUN] {op.dry_run()}"
                logs.append(msg)
                logger.info(msg)
            else:
                try:
                    msg = f"[EXECUTE] {op.dry_run()}"
                    logs.append(msg)
                    logger.info(msg)
                    op.apply()
                except Exception as e:
                    error_msg = f"Failed to execute {op.description} / 执行 {op.description} 失败: {e}"
                    logger.error(error_msg)
                    logs.append(f"[ERROR] {error_msg}")
                    # In a robust system, we might want to rollback or stop here.
                    # For MVP, we stop.
                    raise e
        return logs
