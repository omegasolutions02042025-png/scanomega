import os
import PyPDF2
import docx
import random
import string
from striprtf.striprtf import rtf_to_text

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

