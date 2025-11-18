from typing import Any, Dict, List, Optional

import requests

from src.exceptions import APIError
from src.interfaces import AbsApi


class HeadHunterAPI(AbsApi):
    """
    Класс работы с HeadHunter
    Атрибуты:
        __base_url(str): Базовый url (private);
        __headers(dict): Заголовки запроса (private);
        _endpoint(str): Конечная точка url запроса (protected);
        _params(dict): Параметры запроса (protected);
    Методы:
        __init__(self) -> None:
            Инициализатор экземпляра класса HeadHunterAPI.
        connect(self) -> Dict[Any, Any]:
            Метод подключения к API
        __connect(self) -> Dict[Any, Any]:
            Приватный метод подключения к Head_Hunter_API
            :raise APIError: Ошибка запроса API
            :raise ValueError: Если API выдает не словарь
    """

    def __init__(self) -> None:
        """Инициализация класса HeadHunterAPI"""
        self.__base_url = "https://api.hh.ru"
        self.__headers = {"User-Agent": "HH-User-Agent"}
        self._endpoint = ""
        self._params: Dict[str, Any] = {}
        super().__init__()

    def connect(self, endpoint: Optional[str] = None) -> Dict[Any, Any]:
        """Метод подключения к API"""
        return self.__connect(endpoint)

    def __connect(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Приватный метод подключения к Head_Hunter_API
        :param endpoint: Конечная точка url запроса (по умолчанию None)
        :return: Словарь ответа от API
        :raise APIError: Ошибка запроса API
        :raise ValueError: Если API выдает не словарь
        """
        if endpoint is None:
            endpoint = self._endpoint
        url = f"{self.__base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.__headers, params=self._params)
            if response.status_code != 200:
                error_message = f"Ошибка API: {response.status_code} - {response.text}"
                raise APIError(error_message)
            else:
                result = response.json()
                if not isinstance(result, Dict):
                    raise ValueError("API выдает не словарь")
                return dict(result)
        except requests.RequestException as exc_info:
            raise APIError(f"Ошибка при запросе: {exc_info}")


class HHVacanciesAPI(HeadHunterAPI):
    """
    Подкласс HeadHunterAPI, работы с получение вакансий
        Атрибуты:
            _endpoint(str): Конечная точка url запроса (protected);
            _params(dict): Параметры запроса (protected);
            __vacancies(list): Список вакансий (private)
        Методы:
            __init__(self) -> None:
                Инициализация класса HHVacanciesAPI
            get_vacancies_by_employer_id(self, employer_id: str, max_pages: int = 20) -> List[Dict[str, Any]]:
                Метод получения вакансий по id компании
    """

    def __init__(self) -> None:
        """Инициализация класса HHVacanciesAPI"""
        super().__init__()
        self._endpoint = "/vacancies"
        self._params = {"text": "", "page": 0, "per_page": 100}
        self.__vacancies: List[Dict[str, Any]] = []

    def get_vacancies_by_employer_id(self, employer_id: str, max_pages: int = 20) -> List[Dict[str, Any]]:
        """
        Метод получения вакансий по id компании
        :param employer_id: Идентификатор работодателя
        :param max_pages: Максимальное количество страниц (по умолчанию 20)
        :return: Список словарей вакансий
        """
        self._params["employer_id"] = employer_id
        self._params["page"] = 0
        self.__vacancies.clear()
        while self._params.get("page", 0) < max_pages:
            data = self.connect()
            vacancy = data.get("items", [])
            if not vacancy:
                break
            self.__vacancies.extend(vacancy)
            self._params["page"] += 1  # Увеличение номера страницы

        return self.__vacancies


class HHEmployerAPI(HeadHunterAPI):
    """
    Подкласс HeadHunterAPI, работы с поиском работодателя
        Атрибуты:
            _endpoint(str): Конечная точка url запроса (protected);
            __employer(dict): Словарь информации о работодателе
        Методы:
            __init__(self) -> None:
                Инициализация класса HHEmployerAPI
            get_employer_by_id(self, employer_id: str) -> Dict[str, Any]:
                Метод получения компании по id
    """

    def __init__(self) -> None:
        """Инициализация класса HHEmployerAPI"""
        super().__init__()
        self._endpoint = "/employers/"
        self.__employer: Dict[str, Any] = {}

    def get_employer_by_id(self, employer_id: str) -> Dict[str, Any]:
        """
        Метод получения компании по id
        :param employer_id: ID компании
        :return: Список словарей вакансий
        """
        endpoint_url = f"{self._endpoint}{employer_id}"
        # self._endpoint = f"{self._endpoint}{employer_id}"
        data = self.connect(endpoint_url)
        # data = self.connect()
        self.__employer = data
        return self.__employer


class HHEmployersAPI(HeadHunterAPI):
    """
    Подкласс HeadHunterAPI, работы поиском работодателей
        Атрибуты:
            _endpoint(str): Конечная точка url запроса (protected);
            __employers(list): Список работодателей (private)
        Методы:
            __init__(self) -> None:
                Инициализация класса HHEmployersAPI
            search_employers_id(self, keyword: str) -> List[Dict[str, Any]]:
                Метод поиска компаний по ключевому слову
            get_top_employers(self, top_n: int = 20) -> List[Dict[str, Any]]:
                Метод получения топ n компаний, по количеству открытых вакансий
                :raise TypeError: Аргумент не является числом
                :raise ValueError: Количество должно быть в диапазоне от 1 до 100
    """

    def __init__(self) -> None:
        """Инициализация класса HHEmployersAPI"""
        super().__init__()
        self._endpoint = "/employers"
        self.__employers: List[Dict[str, Any]] = []

    def search_employers_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Метод поиска компаний по ключевому слову
        :param keyword: Ключевое слово
        :return: Список словарей вакансий
        """
        # наличие актуальных вакансий, регионы России
        self._params = {"text": keyword, "only_with_vacancies": "true", "area": "113"}
        self.__employers.clear()
        data = self.connect()
        employers_search = data.get("items", [])
        self.__employers.extend(employers_search)
        return self.__employers

    def get_top_employers(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Метод получения топ n компаний, по количеству открытых вакансий
        :param top_n: Количество вакансий в топе(по умолчанию 20)
        :return: Список словарей вакансий
        :raise TypeError: Аргумент не является числом
        :raise ValueError: Количество должно быть в диапазоне от 1 до 100
        """
        if not isinstance(top_n, int):
            raise TypeError("Аргумент не является числом")
        if top_n > 100:
            raise ValueError("Количество должно быть в диапазоне от 1 до 100")
        self._params = {"per_page": top_n, "sort_by": "by_vacancies_open", "area": "113"}
        self.__employers.clear()
        data = self.connect()
        employers_search = data.get("items", [])
        self.__employers.extend(employers_search)
        return self.__employers
