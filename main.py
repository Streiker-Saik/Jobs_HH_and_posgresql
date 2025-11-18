from src.config import config
from src.database import DBManager
from src.hh_api import HHEmployersAPI
from src.settings import BASE_DIR
from src.utils import (create_database, create_table_employers, create_table_vacancies, df_in_database,
                       get_data_employers, get_data_vacancy_by_employers, safe_data_to_employers,
                       safe_data_to_vacancies)

config_file = BASE_DIR / "database.ini"
db_name = "hh"


def create_database_hh() -> None:
    """Создание базы данных HeadHunter"""
    params = config()
    # создание БД
    create_database(db_name, params)
    # создание таблицы работодателей
    create_table_employers(db_name, params)
    # создание таблицы вакансий
    create_table_vacancies(db_name, params)


def filling_db_hh() -> None:
    """Заполнение БД c API"""
    params = config()
    employers_api = HHEmployersAPI()
    # топ 10 компаний по количеству вакансий
    top_employers = employers_api.get_top_employers(10)
    print(1)
    # получение информации о компаниях по id
    employers_data = get_data_employers(top_employers)
    print(2)
    # получение информации о вакансиях по id компании
    vacancies_data = get_data_vacancy_by_employers(top_employers)
    print(3)
    # запись работодателей в БД
    safe_data_to_employers(employers_data, db_name, params)
    # запись вакансий в БД
    safe_data_to_vacancies(vacancies_data, db_name, params)


def user_interaction_db() -> None:
    """Интерфейс работы с пользователем, работа с БД"""

    db = DBManager(config_file=config_file, section="postgresql_hh")

    user_input = input("Вывести списка вакансий с количеством вакансий? (y/n): ").lower()
    if user_input == "y":
        companies_and_vacancies_count = db.get_companies_and_vacancies_count()
        columns = ["employer_name", "count_vacancies"]
        df = df_in_database(companies_and_vacancies_count, columns)
        print(df)

    user_input = input("Вывести все вакансии? (y/n): ").lower()
    if user_input == "y":
        all_vacancies = db.get_all_vacancies()
        columns = ["employer_name", "vacancy_name", "salary_from", "salary_to", "vacancy_url"]
        df = df_in_database(all_vacancies, columns)
        print(df)

    user_input = input("Вывести среднюю зарплату? (y/n): ").lower()
    if user_input == "y":
        avg_salary = db.get_avg_salary()
        print(avg_salary)

    # получение вакансий у которых зарплата выше средней
    user_input = input("Вывести вакансии у которых зарплата выше средней? (y/n): ").lower()
    if user_input == "y":
        vacancies_with_higher_salary = db.get_vacancies_with_higher_salary()
        columns = ["vacancy_id", "employer_id", "vacancy_name", "city", "vacancy_url", "salary_from", "salary_to"]
        df = df_in_database(vacancies_with_higher_salary, columns)
        print(df)

    # получение вакансий по ключевому слову(-ам)
    user_input = input("Вывести вакансии по ключевым словам? (y/n): ").lower()
    if user_input == "y":
        user_input = input("Введите слово(-а) для поиска в названии у вакансий: ")
        vacancies_with_keyword = db.get_vacancies_with_keyword(user_input)
        columns = ["vacancy_id", "employer_id", "vacancy_name", "city", "vacancy_url", "salary_from", "salary_to"]
        df = df_in_database(vacancies_with_keyword, columns)
        print(df)


if __name__ == "__main__":
    # create_database_hh()
    # filling_db_hh()
    user_interaction_db()
