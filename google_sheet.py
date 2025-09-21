from calendar import c
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import re
import requests
from gspread.utils import a1_to_rowcol, rowcol_to_a1
from funcs import parse_cb_rf, parse_myfin


load_dotenv()

# Настройка Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SHEET_URL = os.getenv('GOOGLE_SHEET_URL')
if not SHEET_URL:
    SHEET_URL = None


def get_google_sheet_client():
    """Получить клиент для работы с Google Sheets"""
    try:
        # Сначала пытаемся использовать переменную окружения
        creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            creds_dict = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        else:
            # Используем файл credentials.json из папки проекта
            credentials_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
            if os.path.exists(credentials_path):
                creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
            else:
                raise FileNotFoundError("Файл credentials.json не найден в папке проекта")
        
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Ошибка при подключении к Google Sheets: {e}")
        return None

def create_or_get_sheet(sheet_name="Resume_Database"):
    """Создать или получить существующую Google таблицу"""
    client = get_google_sheet_client()
    if not client:
        return None
    
    try:
        # Попытаться открыть существующую таблицу
        sheet = client.open(sheet_name)
        worksheet = sheet.sheet1
    except gspread.SpreadsheetNotFound:
        # Создать новую таблицу если не существует
        sheet = client.create(sheet_name)
        worksheet = sheet.sheet1
        
        # Инициализировать заголовки
        headers = [
            "Специализация", 
            "Фамилия",
            "Имя", 
            "Отчество",
            "Грейд",
            "Стэк технологий",
            "Отрасль проекта",
            "Спец опыт",
            "Общий опыт",
            "Уровень Англ.",
            "Доступность",
            "Локация",
            "LinkedIn",
            "Telegram",
            "Телефон",
            "E-mail",
            "Зарплатные ожидания",
            "Рейт (руб)"
        ]
        worksheet.append_row(headers)
        
        # Форматирование заголовков
        worksheet.format('A1:R1', {
            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 0.8},
            'textFormat': {'bold': True}
        })
        
        print(f"Создана новая Google таблица: {sheet_name}")
    
    return worksheet

def create_worksheet(worksheet_name, sheet_url=None, sheet_name="Resume_Database"):
    """Создать новый лист в существующей таблице"""
    client = get_google_sheet_client()
    if not client:
        return None
    
    try:
        if sheet_url:
            sheet = client.open_by_url(sheet_url)
        else:
            sheet = client.open(sheet_name)
        
        # Проверить, существует ли уже лист с таким именем
        existing_worksheets = [ws.title for ws in sheet.worksheets()]
        if worksheet_name in existing_worksheets:
            print(f"Лист '{worksheet_name}' уже существует")
            return sheet.worksheet(worksheet_name)
        
        # Создать новый лист
        worksheet = sheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
        
        # Заголовки не добавляются автоматически при создании листа
        
        print(f"Создан новый лист: {worksheet_name}")
        return worksheet
        
    except Exception as e:
        print(f"Ошибка при создании листа: {e}")
        return None

def get_sheet_by_url(sheet_url, worksheet_name=None):
    """Получить Google таблицу по URL с возможностью выбора конкретного листа"""
    client = get_google_sheet_client()
    if not client:
        return None
    
    try:
        sheet = client.open_by_url(sheet_url)
        
        # Если указано имя листа, использовать его
        if worksheet_name:
            try:
                worksheet = sheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                print(f"Лист '{worksheet_name}' не найден. Создаю новый лист.")
                worksheet = create_worksheet(worksheet_name, sheet_url=sheet_url)
                if not worksheet:
                    return None
        else:
            worksheet = sheet.sheet1
        
        # Заголовки не создаются автоматически
        
        return worksheet
    except Exception as e:
        print(f"Ошибка при открытии таблицы по URL: {e}")
        return None

async def add_data_to_worksheet(data, headers=None, worksheet_name=None):
    """
    Универсальная функция для добавления любых данных в Google таблицу
    
    Args:
        data (dict or list): Данные для добавления (словарь или список значений)
        headers (list): Заголовки столбцов (если None, используются ключи словаря)
        worksheet_name (str): Название листа в таблице
    
    Returns:
        bool: True если успешно добавлено, False если ошибка
    """
    # Получить URL из переменной окружения
    sheet_url = SHEET_URL
    if not sheet_url:
        print("❌ URL таблицы не найден в переменных окружения")
        return False
    
    worksheet = get_sheet_by_url(sheet_url, worksheet_name)
    
    if not worksheet:
        print("Не удалось подключиться к Google Sheets")
        return False
    
    try:
        # Подготовить данные
        if isinstance(data, dict):
            # Если передан словарь
            if not headers:
                headers = list(data.keys())
            
            # Подготовить строку данных
            def format_value(value):
                if value is None or value == '' or value == 'null':
                    return '.'
                return str(value)
            
            row_data = [format_value(data.get(header, '')) for header in headers]
            
        elif isinstance(data, list):
            # Если передан список
            def format_value(value):
                if value is None or value == '' or value == 'null':
                    return '.'
                return str(value)
            
            row_data = [format_value(item) for item in data]
        else:
            print("❌ Неподдерживаемый тип данных. Используйте dict или list")
            return False
        
        # Добавить строку в таблицу
        worksheet.append_row(row_data)
        
        worksheet_info = f" (лист: {worksheet_name})" if worksheet_name else ""
        print(f"✅ Данные успешно добавлены в Google таблицу{worksheet_info}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении данных в Google таблицу: {e}")
        return False


def check_duplicate_by_fio(first_name: str, last_name: str, worksheet_name: str = "Свободные ресурсы на аутстафф") -> bool:
    """
    Проверяет наличие дубликата по ФИ в указанном листе Google таблицы
    
    Args:
        first_name: Имя кандидата
        last_name: Фамилия кандидата  
        worksheet_name: Название листа для поиска
    
    Returns:
        True если найден дубликат, False если не найден или ошибка
    """
    try:
        client = get_google_sheet_client()
        if not client:
            print("❌ Не удалось подключиться к Google Sheets")
            return False
        
        # Получаем таблицу
        if SHEET_URL:
            sheet = client.open_by_url(SHEET_URL)
        else:
            print("❌ URL Google таблицы не настроен")
            return False
        
        # Получаем лист
        try:
            worksheet = sheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            print(f"❌ Лист '{worksheet_name}' не найден")
            return False
        
        # Получаем все данные из листа
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:  # Нет данных кроме заголовков
            return False
        
        # Ищем совпадения по колонкам B (фамилия), C (имя)
        for row_index, row in enumerate(all_values[1:], start=2):  # Пропускаем заголовки
            if len(row) >= 3:  # Убеждаемся что есть колонки A, B, C
                row_last_name = row[1].strip().lower() if len(row) > 1 else ""  # Колонка B
                row_first_name = row[2].strip().lower() if len(row) > 2 else ""  # Колонка C  
                
                # Сравниваем ФИ (приводим к нижнему регистру для сравнения)
                if (last_name and first_name and 
                    row_last_name == last_name.strip().lower() and 
                    row_first_name == first_name.strip().lower()):
                    
                    print(f"✅ Найден дубликат в строке {row_index}: {last_name} {first_name}")
                    return True
        
        print(f"✅ Дубликат не найден для: {last_name} {first_name}")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка при поиске дубликата: {e}")
        return False


def get_all_resume_ids(worksheet_name: str = "Свободные ресурсы на аутстафф") -> List[str]:
    """
    Получает все ID резюме из указанного листа Google таблицы
    
    Args:
        worksheet_name: Название листа для поиска
    
    Returns:
        Список ID резюме
    """
    try:
        client = get_google_sheet_client()
        if not client:
            print("❌ Не удалось подключиться к Google Sheets")
            return []
        
        # Получаем таблицу
        if SHEET_URL:
            sheet = client.open_by_url(SHEET_URL)
        else:
            print("❌ URL Google таблицы не настроен")
            return []
        
        # Получаем лист
        try:
            worksheet = sheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            print(f"❌ Лист '{worksheet_name}' не найден")
            return []
        
        # Получаем все значения из колонки A (ID резюме)
        id_column = worksheet.col_values(1)  # Колонка A
        
        # Убираем заголовок и пустые значения
        resume_ids = [id_val.strip() for id_val in id_column[1:] if id_val.strip()]
        
        print(f"✅ Найдено {len(resume_ids)} ID в листе '{worksheet_name}'")
        return resume_ids
        
    except Exception as e:
        print(f"❌ Ошибка при получении ID резюме: {e}")
        return []


def delete_resume_by_id(resume_id: str) -> bool:
    """
    Удаляет все записи с указанным ID из всех листов Google таблицы
    
    Args:
        resume_id: ID резюме для удаления
    
    Returns:
        True если удаление прошло успешно, False в случае ошибки
    """
    try:
        client = get_google_sheet_client()
        if not client:
            print("❌ Не удалось подключиться к Google Sheets")
            return False
        
        # Получаем таблицу
        if SHEET_URL:
            sheet = client.open_by_url(SHEET_URL)
        else:
            print("❌ URL Google таблицы не настроен")
            return False
        
        deleted_count = 0
        
        # Получаем все листы в таблице
        worksheets = sheet.worksheets()
        
        for worksheet in worksheets:
            try:
                # Получаем все данные из листа
                all_values = worksheet.get_all_values()
                
                if len(all_values) < 2:  # Нет данных кроме заголовков
                    continue
                
                # Ищем строки с нужным ID (обычно в колонке A)
                rows_to_delete = []
                for row_index, row in enumerate(all_values[1:], start=2):  # Пропускаем заголовки
                    if len(row) > 0 and row[0].strip() == resume_id:
                        rows_to_delete.append(row_index)
                
                # Удаляем строки (в обратном порядке, чтобы индексы не сбились)
                for row_index in reversed(rows_to_delete):
                    worksheet.delete_rows(row_index)
                    deleted_count += 1
                    print(f"✅ Удалена строка {row_index} из листа '{worksheet.title}'")
                    
            except Exception as e:
                print(f"⚠️ Ошибка при обработке листа '{worksheet.title}': {e}")
                continue
        
        if deleted_count > 0:
            print(f"✅ Всего удалено {deleted_count} записей с ID {resume_id}")
            return True
        else:
            print(f"⚠️ Записи с ID {resume_id} не найдены")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при удалении записей: {e}")
        return False

def get_sheet_url(sheet_name="Resume_Database"):
    """Получить URL Google таблицы"""
    # Сначала проверить переменную окружения
    sheet_url = os.getenv('GOOGLE_SHEET_URL')
    if sheet_url:
        return sheet_url
    
    client = get_google_sheet_client()
    if not client:
        return None
    
    try:
        sheet = client.open(sheet_name)
        return sheet.url
    except Exception as e:
        print(f"Ошибка при получении URL таблицы: {e}")
        return None

def search_resume_by_field(field_name, search_value, sheet_name="Resume_Database"):
    """
    Поиск резюме по определенному полю
    
    Args:
        field_name (str): Название поля для поиска
        search_value (str): Значение для поиска
        sheet_name (str): Название Google таблицы
    
    Returns:
        list: Список найденных строк
    """
    worksheet = create_or_get_sheet(sheet_name)
    if not worksheet:
        return []
    
    try:
        # Получить все данные
        all_records = worksheet.get_all_records()
        
        # Поиск по полю
        results = []
        for record in all_records:
            if field_name in record and search_value.lower() in str(record[field_name]).lower():
                results.append(record)
        
        return results
        
    except Exception as e:
        print(f"Ошибка при поиске: {e}")
        return []
    
    
    



def find_value_by_column_b(search_value, sheet_url=SHEET_URL, sheet_name="Data_Database", worksheet_name=None):
    """
    Поиск числовой строки в колонке B и возврат значения из колонки J
    
    Args:
        search_value (str or int): Значение для поиска в колонке B
        sheet_url (str): URL Google таблицы
        sheet_name (str): Название Google таблицы
        worksheet_name (str): Название листа в таблице
    
    Returns:
        str or None: Значение из колонки J или None если не найдено
    """
    if sheet_url:
        worksheet = get_sheet_by_url(sheet_url, worksheet_name)
    else:
        worksheet = create_or_get_sheet(sheet_name, worksheet_name)
    
    if not worksheet:
        print("Не удалось подключиться к Google Sheets")
        return None
    
    try:
        # Получить все значения из колонки B
        column_b_values = worksheet.col_values(2)  # Колонка B = индекс 2
        
        # Преобразовать search_value в строку для сравнения
        search_str = str(search_value)
        
        # Найти строку с совпадением
        for row_index, cell_value in enumerate(column_b_values, start=1):
            if str(cell_value) == search_str:
                # Получить значение из колонки J (индекс 10) этой же строки
                try:
                    j_value = worksheet.cell(row_index, 10).value
                    print(f"✅ Найдено значение '{search_value}' в строке {row_index}, колонка J: '{j_value}'")
                    return j_value
                except Exception as e:
                    print(f"❌ Ошибка при получении значения из колонки J: {e}")
                    return None
        
        print(f"❌ Значение '{search_value}' не найдено в колонке B")
        return None
        
    except Exception as e:
        print(f"❌ Ошибка при поиске в таблице: {e}")
        return None


def search_and_extract_values(
    search_column: str, 
    search_value: float, 
    extract_columns: List[str], 
    worksheet_name: str = "Resume_Database"
) -> Optional[Dict[str, Any]]:
    """
    Поиск значения в указанной колонке и извлечение данных из других колонок
    
    Args:
        search_column: Буква колонки для поиска (например, 'B')
        search_value: Числовое значение для поиска
        extract_columns: Список букв колонок для извлечения данных (например, ['A', 'C', 'D'])
        worksheet_name: Название листа
    
    Returns:
        Словарь с найденными значениями или None если ничего не найдено
    """
    try:
        # Получаем клиент и таблицу
        client = get_google_sheet_client()
        if not client:
            return None
        
        # Используем URL из переменной окружения
        if SHEET_URL:
            spreadsheet = client.open_by_url(SHEET_URL)
        else:
            print("❌ GOOGLE_SHEET_URL не установлен в переменных окружения")
            return None
        
        # Выбираем лист по названию
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            print(f"❌ Лист '{worksheet_name}' не найден")
            return None
        
        # Получаем все данные из листа
        all_values = worksheet.get_all_values()
        if not all_values:
            print("❌ Лист пуст")
            return None
        
        # Преобразуем букву колонки в индекс (A=0, B=1, C=2, ...)
        search_col_index = ord(search_column.upper()) - ord('A')
        
        # Создаем диапазон поиска ±40 от искомого значения
        search_range = list(range(int(search_value) - 40, int(search_value) + 41))
        print(f"🔍 Поиск в диапазоне {search_range[0]} - {search_range[-1]} в колонке {search_column}")
        
        target_row_index = None
        exact_match_row = None
        valid_values = []  # Для отладки
        
        for row_index, row in enumerate(all_values):
            if row_index == 0:  # Пропускаем заголовки
                continue
                
            if len(row) <= search_col_index:
                continue
                
            cell_value = row[search_col_index]
            
            if not cell_value:
                continue
                
            try:
                # Пытаемся преобразовать в число
                numeric_value = int(re.sub(r"[^\d]", "", cell_value))
                valid_values.append(numeric_value)  # Для отладки
                
                # Проверяем точное совпадение
                if numeric_value == search_value:
                    exact_match_row = row_index
                    target_row_index = row_index
                    print(f"✅ Найдено точное совпадение: {numeric_value} в строке {row_index + 1}")
                    break
                
                # Проверяем, есть ли это значение в нашем диапазоне поиска
                if int(numeric_value) in search_range:
                    target_row_index = row_index
                    print(f"✅ Найдено первое совпадение: {numeric_value} в строке {row_index + 1}")
                    break  # Берем первое найденное
                    
            except (ValueError, AttributeError):
                continue
        
        # Проверяем результат
        if target_row_index is None:
            print(f"❌ Не найдено значений в диапазоне ±10 от {search_value} в колонке {search_column}")
            print(f"📋 Найденные значения в колонке: {sorted(set(valid_values))[:10]}...")
            return None
        
        target_row = all_values[target_row_index]
        
        # Извлекаем значения из указанных колонок
        result = {
            'found_row': target_row_index + 1,  # +1 для человекочитаемого номера строки
            'search_value_found': target_row[search_col_index] if len(target_row) > search_col_index else '',
            'is_exact_match': exact_match_row is not None,
            'extracted_values': {}
        }
        
        for col_letter in extract_columns:
            col_index = ord(col_letter.upper()) - ord('A')
            if len(target_row) > col_index:
                # Очищаем значение от неразрывных пробелов и других символов
                clean_value = target_row[col_index].replace('\xa0', '').strip()
                result['extracted_values'][col_letter] = clean_value
            else:
                result['extracted_values'][col_letter] = ''
        
        # Выводим только extracted_values
        print(result['extracted_values'])
        
        return result['extracted_values']
        
    except Exception as e:
        print(f"❌ Ошибка при поиске и извлечении данных: {e}")
        return None


def column_letter_to_index(letter: str) -> int:
    """Преобразует букву колонки в индекс (A=0, B=1, ...)"""
    return ord(letter.upper()) - ord('A')


def index_to_column_letter(index: int) -> str:
    """Преобразует индекс в букву колонки (0=A, 1=B, ...)"""
    return chr(ord('A') + index)


def get_all_sheet_headers(sheet_url=None, sheet_name="Resume_Database"):
    """
    Получить заголовки из всех листов кроме первого
    
    Args:
        sheet_url (str): URL Google таблицы
        sheet_name (str): Название Google таблицы
    
    Returns:
        dict: Словарь с названиями листов и их заголовками
    """
    client = get_google_sheet_client()
    if not client:
        return {}
    
    try:
        if sheet_url:
            spreadsheet = client.open_by_url(sheet_url)
        else:
            spreadsheet = client.open(sheet_name)
        
        # Получить все листы кроме первого
        worksheets = spreadsheet.worksheets()[1:]  # Пропускаем первый лист
        
        headers_dict = {}
        
        for worksheet in worksheets:
            try:
                # Получить первую строку (заголовки)
                headers = worksheet.row_values(1)
                if headers:
                    # Фильтруем пустые заголовки
                    clean_headers = [h for h in headers if h.strip()]
                    headers_dict[worksheet.title] = clean_headers
                    print(f"✅ Получены заголовки для листа '{worksheet.title}': {len(clean_headers)} колонок")
                else:
                    print(f"⚠️ Лист '{worksheet.title}' не содержит заголовков")
            except Exception as e:
                print(f"❌ Ошибка при получении заголовков для листа '{worksheet.title}': {e}")
        
        return headers_dict
        
    except Exception as e:
        print(f"❌ Ошибка при получении заголовков листов: {e}")
        return {}


def generate_mapping_variables_from_headers(sheet_url=None, sheet_name="Resume_Database"):
    """
    Создать переменные-маппинги для каждого листа на основе их заголовков
    Ключ и значение одинаковые, ключ в lowercase
    
    Args:
        sheet_url (str): URL Google таблицы
        sheet_name (str): Название Google таблицы
    
    Returns:
        dict: Словарь с переменными-маппингами для каждого листа
    """
    headers_dict = get_all_sheet_headers(sheet_url, sheet_name)
    
    if not headers_dict:
        print("❌ Не удалось получить заголовки листов")
        return {}
    
    mapping_variables = {}
    
    for sheet_title, headers in headers_dict.items():
        # Создаем название переменной на основе названия листа
        var_name = f"{sheet_title.upper().replace(' ', '_').replace('/', '_').replace('-', '_')}_MAP"
        
        # Создаем маппинг где ключ в lowercase, значение оригинальное
        mapping = {}
        for header in headers:
            if header.strip():  # Проверяем что заголовок не пустой
                key = header.lower().strip()
                mapping[key] = header.strip()
        
        mapping_variables[var_name] = mapping
        print(f"✅ Создан маппинг {var_name} с {len(mapping)} элементами")
    
    return mapping_variables


def print_mapping_variables(sheet_url=None, sheet_name="Resume_Database"):
    """
    Вывести код переменных-маппингов для добавления в файл
    
    Args:
        sheet_url (str): URL Google таблицы
        sheet_name (str): Название Google таблицы
    """
    mapping_variables = generate_mapping_variables_from_headers(sheet_url, sheet_name)
    
    if not mapping_variables:
        print("❌ Не удалось создать переменные-маппинги")
        return
    
    print("\n" + "="*50)
    print("ПЕРЕМЕННЫЕ-МАППИНГИ ДЛЯ ДОБАВЛЕНИЯ В maps_for_sheet.py:")
    print("="*50)
    
    for var_name, mapping in mapping_variables.items():
        print(f"\n{var_name} = {{")
        for key, value in mapping.items():
            print(f'    "{key}": "{value}",')
        print("}")
    
    print("\n" + "="*50)
    print("КОНЕЦ ПЕРЕМЕННЫХ-МАППИНГОВ")
    print("="*50)


def update_cell_by_id_and_column(resume_id: str, column_name: str, new_value: str, worksheet_name: str = "Свободные ресурсы на аутстафф") -> bool:
    """
    Обновляет конкретную ячейку в Google таблице по ID резюме и названию колонки
    
    Args:
        resume_id (str): ID резюме для поиска строки
        column_name (str): Название колонки для обновления
        new_value (str): Новое значение для ячейки
        worksheet_name (str): Название листа в таблице
    
    Returns:
        bool: True если обновление прошло успешно, False в случае ошибки
    """
    try:
        client = get_google_sheet_client()
        if not client:
            print("❌ Не удалось подключиться к Google Sheets")
            return False
        
        # Получаем таблицу
        if SHEET_URL:
            sheet = client.open_by_url(SHEET_URL)
        else:
            print("❌ URL Google таблицы не настроен")
            return False
        
        # Получаем лист
        try:
            worksheet = sheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            print(f"❌ Лист '{worksheet_name}' не найден")
            return False
        
        # Получаем все данные из листа
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:  # Нет данных кроме заголовков
            print("❌ В листе нет данных для обновления")
            return False
        
        # Получаем заголовки (первая строка)
        headers = all_values[0]
        
        # Ищем индекс колонки по названию
        column_index = None
        for i, header in enumerate(headers):
            if header.strip().lower() == column_name.strip().lower():
                column_index = i + 1  # +1 для gspread (1-based indexing)
                break
        
        if column_index is None:
            print(f"❌ Колонка '{column_name}' не найдена в заголовках")
            print(f"📋 Доступные колонки: {', '.join(headers)}")
            return False
        
        # Ищем строку с нужным ID (предполагаем что ID в первой колонке)
        target_row_index = None
        for row_index, row in enumerate(all_values[1:], start=2):  # Пропускаем заголовки
            if len(row) > 0 and row[0].strip() == resume_id:
                target_row_index = row_index
                break
        
        if target_row_index is None:
            print(f"❌ Резюме с ID '{resume_id}' не найдено в листе '{worksheet_name}'")
            return False
        
        # Обновляем ячейку
        worksheet.update_cell(target_row_index, column_index, str(new_value))
        print(f"✅ Обновлена ячейка в строке {target_row_index}, колонка '{column_name}': '{new_value}'")
        
        return True
            
    except Exception as e:
        print(f"❌ Ошибка при обновлении ячейки: {e}")
        return False


def update_resume_by_id(resume_id: str, update_data: Dict[str, Any], worksheet_name: str = "Свободные ресурсы на аутстафф") -> bool:
    """
    Обновляет данные резюме в Google таблице по ID
    
    Args:
        resume_id (str): ID резюме для поиска и обновления
        update_data (dict): Словарь с данными для обновления {column_name: new_value}
        worksheet_name (str): Название листа в таблице
    
    Returns:
        bool: True если обновление прошло успешно, False в случае ошибки
    """
    try:
        client = get_google_sheet_client()
        if not client:
            print("❌ Не удалось подключиться к Google Sheets")
            return False
        
        # Получаем таблицу
        if SHEET_URL:
            sheet = client.open_by_url(SHEET_URL)
        else:
            print("❌ URL Google таблицы не настроен")
            return False
        
        # Получаем лист
        try:
            worksheet = sheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            print(f"❌ Лист '{worksheet_name}' не найден")
            return False
        
        # Получаем все данные из листа
        all_values = worksheet.get_all_values()
        
        if len(all_values) < 2:  # Нет данных кроме заголовков
            print("❌ В листе нет данных для обновления")
            return False
        
        # Получаем заголовки (первая строка)
        headers = all_values[0]
        
        # Ищем строку с нужным ID (предполагаем что ID в первой колонке)
        target_row_index = None
        for row_index, row in enumerate(all_values[1:], start=2):  # Пропускаем заголовки
            if len(row) > 0 and row[0].strip() == resume_id:
                target_row_index = row_index
                break
        
        if target_row_index is None:
            print(f"❌ Резюме с ID '{resume_id}' не найдено в листе '{worksheet_name}'")
            return False
        
        # Обновляем данные
        updated_count = 0
        for column_name, new_value in update_data.items():
            try:
                # Ищем индекс колонки по названию
                column_index = None
                for i, header in enumerate(headers):
                    if header.strip().lower() == column_name.strip().lower():
                        column_index = i + 1  # +1 для gspread (1-based indexing)
                        break
                
                if column_index is None:
                    print(f"⚠️ Колонка '{column_name}' не найдена в заголовках")
                    continue
                
                # Обновляем ячейку
                worksheet.update_cell(target_row_index, column_index, str(new_value))
                updated_count += 1
                print(f"✅ Обновлена колонка '{column_name}': '{new_value}'")
                
            except Exception as e:
                print(f"❌ Ошибка при обновлении колонки '{column_name}': {e}")
                continue
        
        if updated_count > 0:
            print(f"✅ Успешно обновлено {updated_count} полей для резюме ID {resume_id} в листе '{worksheet_name}'")
            return True
        else:
            print(f"❌ Не удалось обновить ни одного поля для резюме ID {resume_id}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при обновлении резюме: {e}")
        return False


def generate_and_save_mapping_variables(sheet_url=None, sheet_name="Resume_Database"):
    """
    Генерирует переменные-маппинги и сохраняет их в maps_for_sheet.py
    
    Args:
        sheet_url (str): URL Google таблицы
        sheet_name (str): Название Google таблицы
    
    Returns:
        bool: True если успешно сохранено, False если ошибка
    """
    mapping_variables = generate_mapping_variables_from_headers(sheet_url, sheet_name)
    
    if not mapping_variables:
        print("❌ Не удалось создать переменные-маппинги")
        return False
    
    # Генерируем код для добавления в файл
    code_lines = []
    
    for var_name, mapping in mapping_variables.items():
        code_lines.append(f"\n{var_name} = {{")
        for key, value in mapping.items():
            # Экранируем кавычки в значениях
            escaped_value = value.replace('"', '\\"')
            code_lines.append(f'    "{key}": "{escaped_value}",')
        code_lines.append("}")
    
    # Добавляем код в конец файла maps_for_sheet.py
    try:
        maps_file_path = "maps_for_sheet.py"
        
        # Читаем существующий файл
        with open(maps_file_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Добавляем новые переменные в конец
        new_content = existing_content + "\n\n# Автоматически сгенерированные переменные из заголовков Google Sheets\n"
        new_content += "\n".join(code_lines)
        
        # Записываем обновленный файл
        with open(maps_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Успешно добавлено {len(mapping_variables)} переменных в {maps_file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении в файл: {e}")
        return False




def fill_column_with_sequential_numbers(
    column_letter: str,
    worksheet_name: str = "Свободные ресурсы на аутстафф",
    start_row: int = 2,
    value: int = 0,
) -> bool:
    """
    Заполняет указанную колонку одним и тем же числом во всех строках листа.

    Args:
        column_letter: Буква колонки (например, 'G', 'I').
        worksheet_name: Название листа в таблице.
        start_row: Номер строки, с которой начинать заполнение (обычно 2, чтобы пропустить заголовки).
        value: Число, которое нужно записать во все строки в колонке.

    Returns:
        True если успешно, иначе False.
    """
    try:
        client = get_google_sheet_client()
        if not client:
            print("❌ Не удалось подключиться к Google Sheets")
            return False

        if SHEET_URL:
            sheet = client.open_by_url(SHEET_URL)
        else:
            print("❌ URL Google таблицы не настроен")
            return False

        try:
            worksheet = sheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            print(f"❌ Лист '{worksheet_name}' не найден")
            return False

        all_values = worksheet.get_all_values()
        if not all_values:
            print("❌ Лист пуст")
            return False

        last_row = len(all_values)
        if last_row < start_row:
            print(f"⚠️ В листе нет строк для заполнения начиная с {start_row}")
            return False

        # Формируем значения: одно и то же число в каждой строке
        values = [[value] for _ in range(start_row, last_row + 1)]

        range_a1 = f"{column_letter}{start_row}:{column_letter}{last_row}"
        worksheet.update(range_a1, values)
        print(f"✅ Колонка {column_letter} заполнена значением {value} (строки {start_row}-{last_row}) на листе '{worksheet_name}'")
        return True
    except Exception as e:
        print(f"❌ Ошибка при заполнении колонки: {e}")
        return False

import asyncio

async def update_currency_sheet():
    sheet_names = ['Расчет ставки (штат/контракт) ЕС/США', 'Расчет ставки (штат/контракт) СНГ','Расчет ставки (Самозанятый) СНГ','Расчет ставки (Самозанятый) ЕС/США','Расчет ставки (ИП) СНГ','Расчет ставки (ИП) ЕС/США']
    curses = parse_cb_rf()
    zp = parse_myfin()
    for sheet_name in sheet_names:
        for i in curses:
            
            if i == "USD":
                fill_column_with_sequential_numbers("H", sheet_name, 2, curses[i])
                await asyncio.sleep(3)
            elif i == "EUR":
                fill_column_with_sequential_numbers("I", sheet_name, 2, curses[i])
                await asyncio.sleep(3)
            elif i == "BYN":
                fill_column_with_sequential_numbers("G", sheet_name, 2, curses[i])
                await asyncio.sleep(3)
        fill_column_with_sequential_numbers("J", sheet_name, 2, zp)
        await asyncio.sleep(3)
    await asyncio.sleep(86400)
    
