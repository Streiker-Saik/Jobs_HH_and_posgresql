from unittest.mock import MagicMock, patch

import pytest

from src.database import DBManager
from src.settings import BASE_DIR


def test_config(db_manager: DBManager) -> None:
    """Тест метода config"""
    config_file = BASE_DIR / "database.ini"
    config = db_manager.config(config_file, "postgresql_test")
    assert isinstance(config, dict)
    assert "host" in config


def test_config_error(db_manager: DBManager) -> None:
    """Тест метода config, если секция не найдена"""
    config_file = BASE_DIR / "database.ini"
    with pytest.raises(Exception) as exc_info:
        db_manager.config(config_file, "postgresql_test_non")
    assert f"Section postgresql_test_non is not found in the {config_file} file." == str(exc_info.value)


def test_connect(db_manager: DBManager) -> None:
    """Тест на метод _connect"""
    assert db_manager._DBManager__conn is None  # type: ignore
    db_manager.connect()
    assert db_manager._DBManager__conn is not None  # type: ignore


def test_close(db_manager: DBManager) -> None:
    """Тест на метод __close"""
    db_manager.connect()
    db_manager.close()
    assert db_manager._DBManager__conn is None  # type: ignore


@patch("psycopg2.connect")
def test_get_companies_and_vacancies_count(mock_conn: MagicMock, db_manager: DBManager) -> None:
    """Тест на метод get_companies_and_vacancies_count"""
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [("Компания 1", 5), ("Компания 2", 3)]
    result = db_manager.get_companies_and_vacancies_count()
    assert len(result) == 2
    assert result[0] == ("Компания 1", 5)
    mock_cursor.execute.assert_called_once()


@patch("psycopg2.connect")
def test_get_all_vacancies(mock_conn: MagicMock, db_manager: DBManager) -> None:
    """Тест на метод get_companies_and_vacancies_count"""
    # employer_name, vacancy_name, salary_from, salary_to, vacancy_url
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        ("Компания 1", "Вакансий 1", 10, 20, "url.ru/1"),
        ("Компания 2", "Вакансий 2", 15, 20, "url.ru/2"),
        ("Компания 1", "Вакансий 3", 20, 30, "url.ru/3"),
    ]
    result = db_manager.get_all_vacancies()
    assert len(result) == 3
    assert result[0] == ("Компания 1", "Вакансий 1", 10, 20, "url.ru/1")
    mock_cursor.execute.assert_called_once()


@patch("psycopg2.connect")
def test_get_avg_salary(mock_conn: MagicMock, db_manager: DBManager) -> None:
    """Тест на метод get_avg_salary"""
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ("100.111",)
    result = db_manager.get_avg_salary()
    assert result == 100.111
    mock_cursor.execute.assert_called_once()


@patch("psycopg2.connect")
def test_get_avg_salary_error(mock_conn: MagicMock, db_manager: DBManager) -> None:
    """Тест на метод get_avg_salary если выводиться не число"""
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchone.return_value = ("abc",)
    result = db_manager.get_avg_salary()
    assert result == 0.0


@patch("psycopg2.connect")
def test_get_vacancies_with_higher_salary(mock_conn: MagicMock, db_manager: DBManager) -> None:
    """Тест на метод get_vacancies_with_higher_salary"""
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        (1, "Вакансий 1", 10, 20, "url.ru/1"),
        (2, "Вакансий 2", 15, 20, "url.ru/2"),
        (3, "Вакансий 3", 20, 30, "url.ru/3"),
    ]
    result = db_manager.get_vacancies_with_higher_salary()
    assert len(result) == 3
    assert result[0] == (1, "Вакансий 1", 10, 20, "url.ru/1")
    mock_cursor.execute.assert_called_once()


@patch("psycopg2.connect")
def test_get_vacancies_with_keyword(mock_conn: MagicMock, db_manager: DBManager) -> None:
    """Тест на метод get_vacancies_with_keyword"""
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [(1, "Вакансий 1", 10, 20, "url.ru/1")]
    result = db_manager.get_vacancies_with_keyword("Вакансий 1")
    assert result == [(1, "Вакансий 1", 10, 20, "url.ru/1")]
    mock_cursor.execute.assert_called_once()


def test_get_vacancies_with_keyword_none_keyword(db_manager: DBManager) -> None:
    """Тест на метод get_vacancies_with_keyword при отсутствии поисковых слов"""
    result = db_manager.get_vacancies_with_keyword(" ")
    assert result == []
