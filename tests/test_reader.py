import pytest
from gsheet_utils.reader import _convert_value


def test_convert_value_str():
    assert _convert_value("hello", "str") == "hello"

def test_convert_value_int():
    assert _convert_value("42", "int") == 42

def test_convert_value_float():
    assert _convert_value("3.14", "float") == 3.14

def test_convert_value_date():
    assert str(_convert_value("2025-08-19", "date")) == "2025-08-19"

def test_convert_invalid():
    with pytest.raises(ValueError):
        _convert_value("oops", "int")
