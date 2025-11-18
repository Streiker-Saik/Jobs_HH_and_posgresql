from configparser import ConfigParser
from typing import Any, Dict


def config(file_name: str = "database.ini", section: str = "postgresql") -> Dict[str, Any]:
    """
    Парсинг параметров из файла конфигурации базы данных
    :param file_name: Наименование файла конфигурации (по умолчанию "database.ini")
    :param section: Наименование раздела в файле (по умолчанию "postgresql")
    :return: Словарь параметров для доступа в БД
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
