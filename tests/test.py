from gsheet_utils.reader import read_as_tuples, read_as_dataframe

dict_columns = {"A": "date", "B": "int", "C": "str"}
cred_path = "credentials.json"

SHEET_ID = "1IGEoB46FXM-b7znuc_xj4sb4KKLW7FSce_3EYE4mzfQ"
RANGE = "Лист1!A:C"

print("--- Tuples ---")
print(read_as_tuples(SHEET_ID, RANGE, dict_columns))

print("--- DataFrame ---")
print(read_as_dataframe(SHEET_ID, RANGE, dict_columns))
