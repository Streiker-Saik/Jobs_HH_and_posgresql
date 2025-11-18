from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import psycopg2
from pandas.core.interchange.dataframe_protocol import DataFrame

from src.hh_api import HHEmployerAPI, HHVacanciesAPI


def connect_db(database_name: str, params: Dict[str, Any]) -> Optional[psycopg2.extensions.connection]:
    """
    Подключение к PostgresSQL
    :param database_name: имя БД
    :param params: словарь параметров подключения(host, user, password, port)
    :return: Подключение к БД
    """
    try:
        conn = psycopg2.connect(dbname=database_name, **params)
        print(f"Connected: {database_name}")
        return conn
    except psycopg2.DatabaseError as exc_info:
        print(f"Произошла ошибка {exc_info}")
        return None


def is_database(database_name: str, params: Dict[str, Any]) -> bool:
    """
    Проверка на наличие базы данных
    :param database_name: имя БД
    :param params: словарь параметров подключения(host, user, password, port)
    :return: существует или нет БД
    """
    conn = connect_db("postgres", params)
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT 1 FROM pg_database WHERE datname=%s""", (database_name,))
            exists = cur.fetchone() is not None
        return exists
    finally:
        conn.close()


def create_database(database_name: str, params: Dict[str, Any]) -> None:
    """
    Создание базы данных
    :param database_name: имя БД
    :param params: словарь параметров подключения(host, user, password, port)
    """
    conn = connect_db("postgres", params)
    conn.autocommit = True

    with conn.cursor() as cur:
        if is_database(database_name, params):
            user_input = input(
                "База данных существует. Обновить базу данных с удалением существующей? (y/n): "
            ).lower()
            if user_input == "y":
                # удаление активных подключений
                cur.execute(
                    """
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname=%s AND pid <> pg_backend_pid()
                    """,
                    (database_name,),
                )
                # удаление БД
                cur.execute(f"DROP DATABASE {database_name}")
                # создание БД
                cur.execute(f"CREATE DATABASE {database_name}")
            else:
                print("Работает существующая БД")
        else:
            cur.execute(f"CREATE DATABASE {database_name}")

    conn.close()


def create_table_vacancies(database_name: str, params: Dict[str, Any]) -> None:
    """
    Создание таблицы вакансий
    :param database_name: имя БД
    :param params: словарь параметров подключения(host, user, password, port)
    """
    conn = connect_db(database_name, params)

    try:
        with conn.cursor() as cur:
            if is_database(database_name, params):

                cur.execute(
                    """
                    CREATE TABLE vacancies(
                        vacancy_id SERIAL PRIMARY KEY,
                        employer_id INT REFERENCES employers(employer_id),
                        vacancy_name VARCHAR(100) NOT NULL,
                        city VARCHAR(100) NOT NULL,
                        vacancy_url VARCHAR(255) NOT NULL,
                        salary_from INT,
                        salary_to INT
                    )
                    """
                )
            else:
                print("БД не существует")
            conn.commit()
    except Exception as exc_info:
        print(f"Произошла ошибка {exc_info}")
    finally:
        conn.close()


def create_table_employers(database_name: str, params: Dict[str, Any]) -> None:
    """
    Создание таблицы работодателей
    :param database_name: имя БД
    :param params: словарь параметров подключения(host, user, password, port)
    """
    conn = connect_db(database_name, params)

    try:
        with conn.cursor() as cur:
            if is_database(database_name, params):

                cur.execute(
                    """
                    CREATE TABLE employers(
                        employer_id SERIAL PRIMARY KEY,
                        employer_name VARCHAR(100) UNIQUE NOT NULL,
                        employer_url VARCHAR(100) NOT NULL
                    )
                    """
                )
            conn.commit()
    except Exception as exc_info:
        print(f"Произошла ошибка {exc_info}")
    finally:
        conn.close()


def safe_data_to_employers(data: List[Dict[str, Any]], database_name: str, params: Dict[str, Any]) -> None:
    """
    Заполнение данными БД из списка работодателей
    :param data: Словарь данных о работодателе (ключи: id, name, alternate_url)
    :param database_name: имя БД
    :param params: словарь параметров подключения(host, user, password, port)
    """
    conn = connect_db(database_name, params)

    try:
        with conn.cursor() as cur:
            for employer in data:
                employer_id = employer.get("id")
                name = employer.get("name")
                url = employer.get("alternate_url")
                cur.execute(
                    """
                    INSERT INTO employers (employer_id, employer_name, employer_url)
                    VALUES (%s, %s, %s)
                    """,
                    (
                        employer_id,
                        name,
                        url,
                    ),
                )

        conn.commit()
    except Exception as exc_info:
        print(f"Произошла ошибка {exc_info}")
    finally:
        conn.close()


def safe_data_to_vacancies(data: List[Dict[str, Any]], database_name: str, params: Dict[str, Any]) -> None:
    """
    Заполнение данными БД из списка вакансий
    :param data: Словарь данных о работодателе (
        ключи: id, employer.id, name, area.name, alternate_url, salary_from, salary_to
    )
    :param database_name: имя БД
    :param params: словарь параметров подключения(host, user, password, port)
    """
    conn = connect_db(database_name, params)

    try:
        with conn.cursor() as cur:
            for vacancy in data:
                vacancy_id = vacancy.get("id")
                employer_id = vacancy.get("employer").get("id")
                vacancy_name = vacancy.get("name")
                city = vacancy.get("area").get("name")
                url = vacancy.get("alternate_url")
                salary_info = vacancy.get("salary")
                if salary_info is not None:
                    salary_from = salary_info.get("from")
                    salary_to = salary_info.get("to")
                else:
                    salary_from = None
                    salary_to = None

                cur.execute(
                    """
                    INSERT INTO vacancies (
                        vacancy_id, employer_id, vacancy_name, city, vacancy_url, salary_from, salary_to
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        vacancy_id,
                        employer_id,
                        vacancy_name,
                        city,
                        url,
                        salary_from,
                        salary_to,
                    ),
                )

        conn.commit()
    except Exception as exc_info:
        print(f"Произошла ошибка {exc_info}")
    finally:
        conn.close()


def get_data_employers(employers_id: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Получение данных о компаниях по id
    :param employers_id: Список словарей (ключи: id)
    :return: Список словарей работодателей по id
    """
    employer_data = HHEmployerAPI()
    # employers = [employer_data.get_employer_by_id(employer.get("id")) for employer in employers_id]
    employers = []
    for employer in employers_id:
        employer = employer_data.get_employer_by_id(employer.get("id"))
        employers.append(employer)
    return employers


def get_data_vacancy_by_employers(employers_id: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Получение данных о вакансиях по id компании
    :param employers_id: Список словарей (ключи: id)
    :return: Список словарей вакансий по id
    """
    vacancies_data = HHVacanciesAPI()
    # vacancies_list = [vacancies_data.get_vacancies_by_employer_id(employer.get("id")) for employer in employers_id]
    vacancies_list = []
    for employer in employers_id:
        vacancies = vacancies_data.get_vacancies_by_employer_id(employer.get("id"))
        vacancies_list.extend(vacancies)
    return vacancies_list


def df_in_database(db_data: List[Tuple[Any]], columns_name: List[str]) -> DataFrame:
    """
    Перевод в DataFrame списка кортежей полученных из БД
    :param db_data: Данные полученные из БД
    :param columns_name: наименования столбцов
    :return: DataFrame
    """
    if db_data is None:
        print("Нет данных для отображения.")
    else:
        return pd.DataFrame(db_data, columns=[columns_name])
