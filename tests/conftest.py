import pytest
from typing import Any, Dict
from src.database import DBManager
from src.settings import BASE_DIR


@pytest.fixture
def params_db() -> Dict[str, Any]:
    return {"host": "localhost", "user": "user_name", "password": "password", "port": 5432}


@pytest.fixture
def db_manager() -> DBManager:
    config_file = BASE_DIR / "database.ini"
    return DBManager(config_file=config_file, section="postgresql_test")