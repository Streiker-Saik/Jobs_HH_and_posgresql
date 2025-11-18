from typing import Optional


class APIError(Exception):
    """Исключение, ошибки статуса API"""

    def __init__(self, message: Optional[str] = None) -> None:
        """
        Инициализация исключения APIError
        :param message: Сообщение, описывающее причину исключения (по умолчанию None)
        """
        self.message = message
        super().__init__(message)
