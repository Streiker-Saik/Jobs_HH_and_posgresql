from unittest.mock import MagicMock, patch

import pytest

from src.config import config


@patch("src.config.ConfigParser")
def test_config(mock_parser: MagicMock) -> None:
    """Тестирование получение параметров конфигурации из файла"""
    mock_parser.return_value.has_section.return_value = True
    mock_parser.return_value.items.return_value = [
        ("host", "localhost"),
        ("user", "user_name"),
        ("password", "password"),
        ("port", 5432),
    ]
    expected = {"host": "localhost", "user": "user_name", "password": "password", "port": 5432}
    result = config("test.ini", "postgresql")
    assert result == expected


@patch("src.config.ConfigParser")
def test_config_no_section(mock_parser: MagicMock) -> None:
    """Тестирование получение параметров конфигурации из файла если секция не найдена"""
    mock_parser.return_value.has_section.return_value = False

    with pytest.raises(Exception) as exc_info:
        config("test.ini", "postgresql")

    assert "Section postgresql is not found in the test.ini file." == str(exc_info.value)
