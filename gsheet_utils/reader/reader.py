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
    """Преобразует букву колонки в индекс (A=0, B=1, AA=26, AB=27, ...)"""
    letter = letter.upper()
    result = 0
    for char in letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


def _index_to_col_letter(index: int) -> str:
    """Преобразует индекс в букву колонки (0=A, 1=B, 26=AA, 27=AB, ...)"""
    index += 1
    result = ""
    while index > 0:
        index -= 1
        result = chr(index % 26 + ord('A')) + result
        index //= 26
    return result


def _get_column_range_info(range_name: str) -> Tuple[str, str]:
    """Извлекает начальную и конечную колонки из диапазона, например 'B:E' -> ('B', 'E')"""
    if '!' in range_name:
        range_part = range_name.split('!')[-1]
    else:
        range_part = range_name
    
    if ':' in range_part:
        start_col, end_col = range_part.split(':')
        # Извлекаем только буквенную часть
        start_col = ''.join(c for c in start_col if c.isalpha())
        end_col = ''.join(c for c in end_col if c.isalpha())
        return start_col, end_col
    else:
        col = ''.join(c for c in range_part if c.isalpha())
        return col, col


def _get_columns_in_range(start_col: str, end_col: str) -> List[str]:
    """Возвращает список всех колонок в диапазоне от start_col до end_col"""
    start_idx = _col_letter_to_index(start_col)
    end_idx = _col_letter_to_index(end_col)
    columns = []
    for i in range(start_idx, end_idx + 1):
        columns.append(_index_to_col_letter(i))
    return columns


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
        range_name: Диапазон ячеек (например, "Лист1!B:E")
        dict_columns: Словарь {колонка: тип} (например, {"B": "str", "C": "int"})
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

    start_col, end_col = _get_column_range_info(range_name)
    
    all_range_columns = _get_columns_in_range(start_col, end_col)
    
    column_to_data_index = {}
    for col, dtype in dict_columns.items():
        if col in all_range_columns:
            column_to_data_index[col] = all_range_columns.index(col)
        else:
            column_to_data_index[col] = None 

    rows = []
    for row in values[1:]:
        converted = []
        for col, dtype in dict_columns.items():
            data_idx = column_to_data_index[col]
            if data_idx is not None and data_idx < len(row):
                val = row[data_idx]
            else:
                val = None
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
        range_name: Диапазон ячеек (например, "Лист1!B:E")
        dict_columns: Словарь {колонка: тип} (например, {"B": "str", "C": "int"})
        credentials_path: Путь к файлу credentials.json (по умолчанию)
        credentials_info: Строка JSON или словарь с учетными данными (альтернатива)
    """
    tuples = read_as_tuples(sheet_id, range_name, dict_columns, credentials_path, credentials_info)
    df = pd.DataFrame(tuples, columns=list(dict_columns.keys()))
    return df