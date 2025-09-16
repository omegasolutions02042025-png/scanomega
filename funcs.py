import os
import PyPDF2
import docx
import random
import string
from striprtf.striprtf import rtf_to_text
from bs4 import BeautifulSoup

async def process_pdf(file_path: str) -> str:
    """Извлекает текст из PDF"""
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    
    # Удаляем пустые строки
    lines = text.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

async def process_docx(file_path: str) -> str:
    """Извлекает текст из DOCX"""
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    
    # Удаляем пустые строки
    lines = text.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

async def process_rtf(file_path: str) -> str:
    """Извлекает текст из RTF"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        rtf_content = f.read()
    
    # Конвертируем RTF в текст
    text = rtf_to_text(rtf_content)
    
    # Удаляем пустые строки
    lines = text.split('\n')
    non_empty_lines = [line.strip() for line in lines if line.strip()]
    print('\n'.join(non_empty_lines))
    return '\n'.join(non_empty_lines)

async def process_txt(file_path: str) -> str:
    """Извлекает текст из TXT"""
    try:
        # Пробуем разные кодировки
        encodings = ['utf-8', 'cp1251', 'windows-1251', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue
        else:
            # Если все кодировки не сработали, используем utf-8 с игнорированием ошибок
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
    
        # Удаляем пустые строки
        lines = text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        return '\n'.join(non_empty_lines)
    
    except Exception as e:
        raise Exception(f"Ошибка при чтении TXT файла: {str(e)}") 


def generate_random_id():
    letter = random.choice(string.ascii_lowercase)  # случайная буква a-z
    number = random.randint(10000, 99999)           # случайное число 10000-99999
    return f"{letter}_{number}"


def build_row(resume_id: str, data: dict, MAP: dict) -> dict:
    """
    Преобразует словарь data в строку для Google Sheets.
    
    :param resume_id: ID кандидата
    :param data: {"Английский": "B2", "немецкий": "A2", "english": "C1", ...}
    :param MAP: словарь соответствий {русский/английский lowercase : English}
    :return: dict для вставки в таблицу
    """
    row = {"ID кандидата": resume_id}

    # Проверяем, что data не None
    if data is None:
        data = {}

    # нормализуем входящие ключи
    normalized = {k.lower(): v for k, v in data.items()}

    for key, eng_name in MAP.items():
        if key in normalized:
            value = normalized[key]
            # Заменяем false на крестик
            if value is False or value is None:
                row[eng_name.lower()] = "❌"
            else:
                row[eng_name.lower()] = value

    return row


def build_row_symbols(resume_id: str, data: dict, MAP: dict) -> dict:
    """
    Преобразует словарь data в строку для Google Sheets с заменой boolean значений на символы.
    
    :param resume_id: ID кандидата
    :param data: {"Английский": "B2", "немецкий": "A2", "english": "C1", "programming": True, "management": False, ...}
    :param MAP: словарь соответствий {русский/английский lowercase : English}
    :return: dict для вставки в таблицу с "+" для True и "-" для False
    """
    row = {"ID кандидата": resume_id}

    # Проверяем, что data не None
    if data is None:
        data = {}

    # нормализуем входящие ключи
    normalized = {k.lower(): v for k, v in data.items()}

    for key, eng_name in MAP.items():
        if key in normalized:
            value = normalized[key]
            # Заменяем boolean значения на символы
            if isinstance(value, bool):
                row[eng_name.lower()] = "✅" if value else "❌"
            else:
                row[eng_name.lower()] = value

    return row


import requests

def parse_vsebanki():
    
    try:
        url = "https://www.banki.ru/products/currency/cb/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.banki.ru/products/currency/cb/",
            "X-Requested-With": "XMLHttpRequest"
        }
        response = requests.get(url, headers=headers)
        print(response.url)       # вдруг редиректит на заглушку
        print(response.status_code)
        print(len(response.text))
        
        soup = BeautifulSoup(response.text, 'html.parser')
        usd_currency = soup.find('div', {'data-id': '840'}).find('div', {'class': 'FlexboxGridItem__sc-1crr98y-0 fQGtRy'}).find('div', {'class': 'Text__sc-vycpdy-0 gJTmbP'}).text.replace(" ", "").replace("₽", "").replace(",", ".")
        eur_currency = soup.find('div', {'data-id': '978'}).find('div', {'class': 'FlexboxGridItem__sc-1crr98y-0 fQGtRy'}).find('div', {'class': 'Text__sc-vycpdy-0 gJTmbP'}).text.replace(" ", "").replace("₽", "").replace(",", ".")
        byn_currency = soup.find('div', {'data-id': '933'}).find('div', {'class': 'FlexboxGridItem__sc-1crr98y-0 fQGtRy'}).find('div', {'class': 'Text__sc-vycpdy-0 gJTmbP'}).text.replace(" ", "").replace("₽", "").replace(",", ".")
        
        return {'USD': float(usd_currency), 'EUR': float(eur_currency), 'BYN': float(byn_currency)}
    except Exception as e:
        print(f"Error parsing vsebanki: {e}")
        return None
        


def parse_myfin():
    try:
        url = "https://myfin.by/wiki/term/srednyaya-zarplata-v-belarusi"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.banki.ru/products/currency/cb/",
            "X-Requested-With": "XMLHttpRequest"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        zp = soup.find('div', {'class': 'information-block__current-value x__current-value--mr'}).text.replace(" ", "").replace("рублей", "").replace(",", ".").replace("\n", "")
        return float(zp)
    except Exception as e:
        print(f"Error parsing myfin: {e}")
        return None


def json_get_vse_banki():
    

    import requests

    url = "https://www.banki.ru/products/currencyNodejsApi/getCbrCurrenciesResources/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.banki.ru/products/currency/cb/",
        "X-Requested-With": "XMLHttpRequest"
    }

    r = requests.get(url, headers=headers)
    print("Content-Type:", r.headers.get("Content-Type"))
    print(r.text[:700])  # первые 200 символов

    try:
        data = r.json()
        for item in data:
            print(f"{item['code']} ({item['name']}): {item['value']}")
    except Exception as e:
        print("Не JSON, а HTML:", e)



parse_myfin()
parse_vsebanki()


json_get_vse_banki()





