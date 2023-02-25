"""Working with internal data flow (users, requests billing, etc.)"""

import db_access
from datetime import datetime
from typing import Tuple

def check_user(external_user_id: int) -> int:
    """check if user exists in the db, create if not and return id"""
    id = db_access.check_id("users","external_user_id", external_user_id)
    if id == 0:
        id = _add_user(external_user_id)
    return id

def get_user_data(ext_user_id: int, column: str):
    return db_access.fetch_value("users", ext_user_id, column)

def add_user_data(ext_user_id: int, column_value: Tuple) -> int:
    "Add data to user"
    db_access.update_value("users",ext_user_id,(f"{column_value[0]}",column_value[1]))

def _add_user(external_user_id: int) -> int:
    "Add new user"
    id = db_access.insert("users", {
            "external_user_id": external_user_id,
            "created": datetime.now().timestamp()
    })
    return id

