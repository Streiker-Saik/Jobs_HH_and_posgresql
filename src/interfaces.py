from abc import ABC, abstractmethod
from typing import Any, Dict


class AbsApi(ABC):
    """
    Абстрактный класс работы с API
        connect(self) -> Dict[Any, Any]:
            Метод подключения к API
    """

    @abstractmethod
    def connect(self) -> Dict[Any, Any]:
        """Метод подключения к API"""
        pass


class AbsPostgresSQL(ABC):
    """
    Абстрактный класс работы с PostgresSQL
        connect(self) -> None:
            Метод подключения к API
    """

    @abstractmethod
    def connect(self) -> None:
        """Метод подключение к БД"""
        pass
