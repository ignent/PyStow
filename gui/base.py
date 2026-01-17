from abc import ABC, abstractmethod
from typing import List
from core.models import Package
from core.executor import OperationPlan

class UserInterface(ABC):
    """用户界面抽象基类。"""
    @abstractmethod
    def show_packages(self, packages: List[Package]) -> None:
        """显示包列表。"""
        pass

    @abstractmethod
    def show_plan(self, plan: OperationPlan) -> None:
        """显示操作计划。"""
        pass

    @abstractmethod
    def confirm(self, message: str) -> bool:
        """请求确认。"""
        pass

    @abstractmethod
    def show_message(self, message: str) -> None:
        """显示消息。"""
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        """显示错误。"""
        pass
