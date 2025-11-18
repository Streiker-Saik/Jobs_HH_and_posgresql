import pathlib
from configparser import ConfigParser
from typing import Any, Dict, List, Tuple, Union, Optional

import psycopg2

from src.interfaces import AbsPostgresSQL


class DBManager(AbsPostgresSQL):
    """
    Класс работы с БД PostgresSQL

    Атрибуты:
        config_file(str): Полный путь к файлу конфигурации (по умолчанию "database.ini");
        section(str): Наименование раздела в файле (по умолчанию "postgresql");
        __config(str): Параметры БД(private);
        __host(str): Владелец БД, по умолчанию "localhost"(private);
        __user(str): Пользователь БД, по умолчанию "postgres"(private);
        __port(int): Порт БД, по умолчанию 5432(private);
        __database(str): Наименование БД, по умолчанию "postgres"(private);
        __password(str): Пароль БД, по умолчанию None(private);
        __conn(str): Подключение к БД(private)

    Методы:
        __init__(self, config_file: str = "database.ini", section: str = "postgresql") -> None:
            Инициализация класса DBManager
        config(file_name="database.ini", section="postgresql") -> Dict[str, Any]:
            Статический метод: парсинг параметров из файла конфигурации базы данных
        connect(self) -> None:
            Метод подключение к БД
        close(self) -> None:
            Метод закрытия подключения к БД
        get_companies_and_vacancies_count(self) -> List[Tuple[Any]]:
            Метод получает список всех компаний и количество вакансий у каждой компании
            :raise psycopg2.DatabaseError: Ошибка запроса в БД
        get_all_vacancies(self) -> List[Tuple[Any]]:
            Метод получает список всех вакансий с указанием названия компании,
            названия вакансии, зарплаты от, зарплаты до и ссылки на вакансию
            :raise psycopg2.DatabaseError: Ошибка запроса в БД
        get_avg_salary(self) -> float:
            Метод получает среднюю зарплату по вакансиям
            :raise psycopg2.DatabaseError: Ошибка запроса в БД
            :raise ValueError: Результат не является числом
        get_vacancies_with_higher_salary(self) -> List[Tuple[Any]]:
            Метод получает список всех вакансий, у которых зарплата выше средней по всем вакансиям
            :raise psycopg2.DatabaseError: Ошибка запроса в БД
        get_vacancies_with_keyword(self, keywords: str) -> List[Tuple[Any]]:
            Метод получает список всех вакансий, в названии которых содержатся переданные в метод слова
            :raise psycopg2.DatabaseError: Возникает, если произошла ошибка при выполнении запроса в базу данных
    """

    config_file: str
    section: str

    def __init__(self, config_file: Union[pathlib.Path, str] = "database.ini", section: str = "postgresql") -> None:
        """
        Инициализация класса DBManager
        :param config_file: Полный путь к файлу конфигурации (по умолчанию "database.ini")
        :param section: Наименование раздела в файле (по умолчанию "postgresql")
        """
        self.__config = self.config(config_file, section)
        self.__host = self.__config.get("host", "localhost")
        self.__user = self.__config.get("user", "postgres")
        self.__port = self.__config.get("port", 5432)
        self.__database = self.__config.get("dbname", "postgres")
        self.__password = self.__config.get("password", None)
        self.__conn: Optional[psycopg2.extensions.connection] = None

    @staticmethod
    def config(file_name: Union[pathlib.Path, str] = "database.ini", section: str = "postgresql") -> Dict[str, Any]:
        """
        Парсинг параметров из файла конфигурации базы данных
        :param file_name: Наименование файла конфигурации
        :param section: Наименование раздела в файле
        :return: Словарь параметров подключения к БД
        """
        parser = ConfigParser()
        parser.read(file_name)
        db = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                db[param[0]] = param[1]
        else:
            raise Exception("Section {0} is not found in the {1} file.".format(section, file_name))
        return db

    def connect(self) -> None:
        """Метод подключение к БД"""
        if self.__conn is None:
            try:
                self.__conn = psycopg2.connect(
                    host=self.__host,
                    user=self.__user,
                    port=self.__port,
                    dbname=self.__database,
                    password=self.__password,
                )
            except psycopg2.DatabaseError as exc_info:
                print(f"Ошибка подключения: {exc_info}")
                self.__conn = None
        else:
            print("Подключение уже установлено")

    def close(self) -> None:
        """Метод закрытия подключения к БД"""
        if self.__conn is not None:
            self.__conn.close()
            self.__conn = None

    def get_companies_and_vacancies_count(self) -> List[Tuple[Any]]:
        """
        Метод получает список всех компаний и количество вакансий у каждой компании
        :return: Список кортежей, содержащая данные наименование компании и количество вакансий у компании
        :raise psycopg2.DatabaseError: Возникает, если произошла ошибка при выполнении запроса в базу данных
        """
        self.connect()
        try:
            with self.__conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT employer_name, COUNT(vacancy_id) AS count_vacancies
                    FROM employers
                    LEFT JOIN vacancies USING(employer_id)
                    GROUP BY employer_name;
                    """
                )
                result = cur.fetchall()
                return result if result else []
        except psycopg2.DatabaseError as exc_info:
            print(f"Произошла ошибка: {exc_info}")
            return []
        finally:
            self.close()

    def get_all_vacancies(self) -> List[Tuple[Any]]:
        """
        Метод получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты от, зарплаты до и ссылки на вакансию
        :return: Список кортежей, содержащая данные о вакансиях (
            названия компании, названия вакансии, зарплаты от, зарплаты до, ссылка на вакансию
        )
        :raise psycopg2.DatabaseError: Возникает, если произошла ошибка при выполнении запроса в базу данных
        """
        self.connect()
        try:
            with self.__conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT employer_name, vacancy_name, salary_from, salary_to, vacancy_url
                    FROM vacancies
                    LEFT JOIN employers USING(employer_id)
                    """
                )
                result = cur.fetchall()
                return result if result else []
        except psycopg2.DatabaseError as exc_info:
            print(f"Произошла ошибка: {exc_info}")
            return []
        finally:
            self.close()

    def get_avg_salary(self) -> float:
        """
        Метод получает среднюю зарплату по вакансиям
        :return: Средняя зарплата. Если данных нет, возвращает 0.0.
        :raise psycopg2.DatabaseError: Возникает, если произошла ошибка при выполнении запроса в базу данных
        :raise ValueError: Возникает, если произошла результат не является числом
        """
        self.connect()
        try:
            with self.__conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT AVG((salary_from + salary_to)/2) AS avg_salary
                    FROM vacancies
                    """
                )
                result = cur.fetchone()[0]
            return float(result) if result else 0.0
        except psycopg2.DatabaseError as exc_info:
            print(f"Произошла ошибка: {exc_info}")
            return 0.0
        except ValueError:
            print("Получено не числовое значение")
            return 0.0
        finally:
            self.close()

    def get_vacancies_with_higher_salary(self) -> List[Tuple[Any]]:
        """
        Метод получает список всех вакансий, у которых зарплата выше средней по всем вакансиям
        :return: Список кортежей, содержащая данные о вакансиях, зарплата выше средней
        :raise psycopg2.DatabaseError: Возникает, если произошла ошибка при выполнении запроса в базу данных
        """
        self.connect()
        try:
            with self.__conn.cursor() as cur:
                cur.execute(
                    """
                    WITH avg_salary AS (SELECT (AVG(salary_from + salary_to))/2 AS avg_salary FROM vacancies)
                    SELECT vacancy_id, employer_id, vacancy_name, city, vacancy_url, salary_from, salary_to
                    FROM vacancies
                    WHERE ((salary_from+salary_to)/2) > (SELECT avg_salary FROM avg_salary);
                    """
                )
                result = cur.fetchall()
                return result if result else []
        except psycopg2.DatabaseError as exc_info:
            print(f"Произошла ошибка: {exc_info}")
            return []
        finally:
            self.close()

    def get_vacancies_with_keyword(self, keywords: str) -> List[Tuple[Any]]:
        """
        Метод получает список всех вакансий, в названии которых содержатся переданные в метод слова
        :param keywords: Строка с ключевыми словами (разделенная пробелами)
        :return: Список кортежей, содержащая данные о вакансиях, соответствующая условиям поиска
        :raise psycopg2.DatabaseError: Возникает, если произошла ошибка при выполнении запроса в базу данных
        """
        if not keywords.split():
            return []
        keywords_list = keywords.split()
        self.connect()
        try:
            with self.__conn.cursor() as cur:
                conditions = " AND ".join(["LOWER(vacancy_name) LIKE LOWER(%s)" for _ in keywords_list])
                query = (f"SELECT vacancy_id, employer_id, vacancy_name, city, vacancy_url, salary_from, salary_to "
                         f"FROM vacancies WHERE {conditions}")
                vars = tuple(f"%{keyword}%" for keyword in keywords_list)
                cur.execute(query, vars)
                result = cur.fetchall()
                return result if result else []
        except psycopg2.DatabaseError as exc_info:
            print(f"Произошла ошибка: {exc_info}")
            return []
        finally:
            self.close()
