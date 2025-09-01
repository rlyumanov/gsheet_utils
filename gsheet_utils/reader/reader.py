import os
import json
import datetime
from typing import List, Tuple, Dict, Optional, Union

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build


def _parse_date(value: str) -> datetime.date:
    formats = [
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%d.%m.%Y",
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Не удалось распознать дату: '{value}'")


# Поддерживаемые типы
_TYPE_CASTERS = {
    "str": str,
    "int": int,
    "float": float,
    "date": _parse_date,
}


def _convert_value(value: str, dtype: str):
    if value in ("", None):
        return None
    try:
        return _TYPE_CASTERS[dtype](value)
    except Exception as e:
        raise ValueError(f"Ошибка преобразования '{value}' в {dtype}: {e}")


def _col_letter_to_index(letter: str) -> int:
    """A -> 0, B -> 1, ..."""
    return ord(letter.upper()) - ord("A")


def _get_credentials(credentials_path: str = "credentials.json", credentials_info: Optional[Union[str, Dict]] = None):
    """
    Получает учетные данные из файла или строки.
    
    Args:
        credentials_path: Путь к файлу credentials.json
        credentials_info: Строка JSON или словарь с учетными данными
    
    Returns:
        Credentials object
    """
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    
    if credentials_info is not None:
        if isinstance(credentials_info, str):
            credentials_dict = json.loads(credentials_info)
        else:
            credentials_dict = credentials_info
        return service_account.Credentials.from_service_account_info(credentials_dict, scopes=scopes)
    else:
        return service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)


def read_as_tuples(
    sheet_id: str,
    range_name: str,
    dict_columns: Dict[str, str],
    credentials_path: str = "credentials.json",
    credentials_info: Optional[Union[str, Dict]] = None
) -> List[Tuple]:
    """
    Читает Google Sheet и возвращает список кортежей с типизацией.
    
    Args:
        sheet_id: ID Google Sheet
        range_name: Диапазон ячеек (например, "Лист1!A1:E10")
        dict_columns: Словарь {колонка: тип} (например, {"A": "str", "B": "int"})
        credentials_path: Путь к файлу credentials.json (по умолчанию)
        credentials_info: Строка JSON или словарь с учетными данными (альтернатива)
    """
    creds = _get_credentials(credentials_path, credentials_info)
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    values = result.get("values", [])

    if not values:
        return []

    col_indices = {col: _col_letter_to_index(col) for col in dict_columns}

    rows = []
    for row in values[1:]:
        converted = []
        for col, dtype in dict_columns.items():
            idx = col_indices[col]
            val = row[idx] if idx < len(row) else None
            converted.append(_convert_value(val, dtype))
        rows.append(tuple(converted))

    return rows


def read_as_dataframe(
    sheet_id: str,
    range_name: str,
    dict_columns: Dict[str, str],
    credentials_path: str = "credentials.json",
    credentials_info: Optional[Union[str, Dict]] = None
) -> pd.DataFrame:
    """
    Читает Google Sheet и возвращает DataFrame с типизацией.
    
    Args:
        sheet_id: ID Google Sheet
        range_name: Диапазон ячеек (например, "Sheet1!A1:E10")
        dict_columns: Словарь {колонка: тип} (например, {"A": "str", "B": "int"})
        credentials_path: Путь к файлу credentials.json (по умолчанию)
        credentials_info: Строка JSON или словарь с учетными данными (альтернатива)
    """
    tuples = read_as_tuples(sheet_id, range_name, dict_columns, credentials_path, credentials_info)
    df = pd.DataFrame(tuples, columns=list(dict_columns.keys()))
    return df