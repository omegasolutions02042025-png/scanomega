import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor
from google_disk import GoogleDriveManager
from typing import Optional, Dict, Any
import logging
import urllib.request
import tempfile
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для отслеживания регистрации шрифтов
_fonts_registered = False

def register_fonts():
    """Регистрирует шрифты для поддержки кириллицы"""
    global _fonts_registered
    if _fonts_registered:
        return
    
    try:
        # Пытаемся использовать системные шрифты Windows
        if os.name == 'nt':  # Windows
            # Пути к системным шрифтам Windows
            font_paths = [
                r'C:\Windows\Fonts\arial.ttf',
                r'C:\Windows\Fonts\calibri.ttf',
                r'C:\Windows\Fonts\times.ttf',
                r'C:\Windows\Fonts\tahoma.ttf'
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font_name = os.path.basename(font_path).replace('.ttf', '')
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    logger.info(f"Зарегистрирован шрифт: {font_name}")
                    _fonts_registered = True
                    return font_name
        
        # Если системные шрифты не найдены, используем DejaVu Sans (поддерживает кириллицу)
        # Скачиваем шрифт во временную папку
        temp_dir = tempfile.gettempdir()
        font_path = os.path.join(temp_dir, 'DejaVuSans.ttf')
        
        if not os.path.exists(font_path):
            font_url = 'https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf'
            urllib.request.urlretrieve(font_url, font_path)
            logger.info("Скачан шрифт DejaVu Sans")
        
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        logger.info("Зарегистрирован шрифт DejaVu Sans")
        _fonts_registered = True
        return 'DejaVuSans'
        
    except Exception as e:
        logger.warning(f"Не удалось зарегистрировать кириллические шрифты: {e}")
        # Возвращаем стандартный шрифт
        _fonts_registered = True
        return 'Helvetica'

def create_styled_pdf_styles(font_name: str):
    """Создает набор стилей для резюме с корпоративной цветовой схемой"""
    styles = getSampleStyleSheet()
    
    # Основные цвета
    PRIMARY_BLUE = HexColor('#4A90E2')  # Голубой для заголовков секций
    BLACK = HexColor('#000000')
    DARK_GRAY = HexColor('#333333')
    GRAY = HexColor('#555555')
    
    custom_styles = {
        'title': ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=DARK_GRAY,
            fontName=font_name or 'Helvetica'
        ),
        
        'section_header': ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=20,
            alignment=TA_LEFT,
            textColor=PRIMARY_BLUE,
            fontName=font_name or 'Helvetica-Bold'
        ),
        
        'subheader': ParagraphStyle(
            'SubHeader',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=6,
            spaceBefore=8,
            alignment=TA_LEFT,
            textColor=BLACK,
            fontName=font_name or 'Helvetica-Bold'
        ),
        
        'body': ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            alignment=TA_LEFT,
            textColor=BLACK,
            fontName=font_name or 'Helvetica'
        ),
        
        'secondary': ParagraphStyle(
            'SecondaryText',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT,
            textColor=GRAY,
            fontName=font_name or 'Helvetica'
        )
    }
    
    return custom_styles

def process_styled_text(text: str, styles: dict) -> list:
    """Обрабатывает текст с HTML-тегами стилизации и возвращает список элементов для PDF"""
    story = []
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        if paragraph.strip():
            safe_paragraph = paragraph.strip()
            
            # Обрабатываем <br> теги - заменяем на пустые строки или удаляем
            if safe_paragraph == '<br>' or safe_paragraph == '<br/>':
                story.append(Spacer(1, 6))
                continue
            
            # Удаляем проблемные символы ■ которые появляются вместо кириллицы
            safe_paragraph = safe_paragraph.replace('■', '')
            # Убираем лишние пробелы
            safe_paragraph = ' '.join(safe_paragraph.split())
            
            # Дополнительная очистка от других проблемных символов
            safe_paragraph = safe_paragraph.replace('\ufffd', '')  # Символ замещения Unicode
            safe_paragraph = safe_paragraph.replace('\u25a0', '')  # Черный квадрат
            
            # Удаляем одиночные <br> теги
            safe_paragraph = re.sub(r'<br\s*/?>', '', safe_paragraph, flags=re.IGNORECASE)
            
            # Определяем стиль на основе содержимого
            current_style = styles['body']
            
            # Проверяем, является ли это заголовком секции (содержит HTML теги с цветом #4A90E2)
            if re.search(r'<b color="#4A90E2">', safe_paragraph, re.IGNORECASE):
                current_style = styles['section_header']
                # Убираем HTML теги для заголовков секций, так как стиль уже применен
                safe_paragraph = re.sub(r'<b color="#4A90E2">(.*?)</b>', r'\1', safe_paragraph, flags=re.IGNORECASE)
            # Проверяем, является ли это подзаголовком (содержит <b> без цвета)
            elif re.search(r'<b>(?!.*color)', safe_paragraph, re.IGNORECASE):
                current_style = styles['subheader']
                # Убираем HTML теги для подзаголовков, так как стиль уже применен
                safe_paragraph = re.sub(r'<b>(.*?)</b>', r'\1', safe_paragraph, flags=re.IGNORECASE)
            # Проверяем, содержит ли вторичный текст (цвет #555555)
            elif re.search(r'color="#555555"', safe_paragraph, re.IGNORECASE):
                current_style = styles['secondary']
            # Проверяем, содержит ли технологии (цвет #4A90E2 без bold) - теперь делаем их чёрными
            elif re.search(r'<font color="#4A90E2">', safe_paragraph, re.IGNORECASE):
                current_style = styles['body']
                # Заменяем цветные теги на обычный чёрный текст
                safe_paragraph = re.sub(r'<font color="#4A90E2">(.*?)</font>', r'\1', safe_paragraph, flags=re.IGNORECASE)
            
            if safe_paragraph:
                story.append(Paragraph(safe_paragraph, current_style))
        else:
            story.append(Spacer(1, 6))
    
    return story

def create_pdf_from_text(text: str, output_path: str, title: str = "Документ", use_styling: bool = True) -> bool:
    """
    Создает PDF файл из текста с поддержкой стилизации
    
    Args:
        text: Текст для записи в PDF (может содержать HTML-теги для стилизации)
        output_path: Путь для сохранения PDF файла
        title: Заголовок документа
        use_styling: Использовать ли корпоративную стилизацию
    
    Returns:
        True если файл создан успешно, False в случае ошибки
    """
    try:
        # Регистрируем шрифты для поддержки кириллицы
        font_name = register_fonts()
        
        # Создаем директорию если она не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Создаем документ
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        if use_styling:
            # Используем новую стилизованную систему
            custom_styles = create_styled_pdf_styles(font_name)
            
            # Создаем содержимое
            story = []
            
            # Добавляем заголовок
            safe_title = title.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            story.append(Paragraph(safe_title, custom_styles['title']))
            story.append(Spacer(1, 12))
            
            # Обрабатываем стилизованный текст
            styled_content = process_styled_text(text, custom_styles)
            story.extend(styled_content)
        else:
            # Используем старую систему для обратной совместимости
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor='black',
                fontName=font_name or 'Helvetica'
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                alignment=TA_JUSTIFY,
                textColor='black',
                fontName=font_name or 'Helvetica'
            )
            
            story = []
            safe_title = title.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            story.append(Paragraph(safe_title, title_style))
            story.append(Spacer(1, 12))
            
            paragraphs = text.split('\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    safe_paragraph = paragraph.strip()
                    safe_paragraph = safe_paragraph.replace('■', ' ')
                    safe_paragraph = ' '.join(safe_paragraph.split())
                    safe_paragraph = safe_paragraph.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                    if safe_paragraph:
                        story.append(Paragraph(safe_paragraph, body_style))
                else:
                    story.append(Spacer(1, 6))
        
        # Создаем PDF
        doc.build(story)
        
        logger.info(f"PDF файл успешно создан: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка создания PDF файла: {e}")
        return False

def create_pdf_bytes_from_text(text: str, title: str = "Документ", use_styling: bool = True) -> Optional[bytes]:
    """
    Создает PDF файл из текста и возвращает его в виде байтов с поддержкой стилизации
    
    Args:
        text: Текст для записи в PDF (может содержать HTML-теги для стилизации)
        title: Заголовок документа
        use_styling: Использовать ли корпоративную стилизацию
    
    Returns:
        Байты PDF файла или None в случае ошибки
    """
    try:
        # Регистрируем шрифты для поддержки кириллицы
        font_name = register_fonts()
        
        # Создаем буфер в памяти
        buffer = io.BytesIO()
        
        # Создаем документ
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        if use_styling:
            # Используем новую стилизованную систему
            custom_styles = create_styled_pdf_styles(font_name)
            
            # Создаем содержимое
            story = []
            
            # Добавляем заголовок
            safe_title = title.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            story.append(Paragraph(safe_title, custom_styles['title']))
            story.append(Spacer(1, 12))
            
            # Обрабатываем стилизованный текст
            styled_content = process_styled_text(text, custom_styles)
            story.extend(styled_content)
        else:
            # Используем старую систему для обратной совместимости
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor='black',
                fontName=font_name or 'Helvetica'
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                alignment=TA_JUSTIFY,
                textColor='black',
                fontName=font_name or 'Helvetica'
            )
            
            story = []
            safe_title = title.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
            story.append(Paragraph(safe_title, title_style))
            story.append(Spacer(1, 12))
            
            paragraphs = text.split('\n')
            for paragraph in paragraphs:
                if paragraph.strip():
                    safe_paragraph = paragraph.strip()
                    safe_paragraph = safe_paragraph.replace('■', ' ')
                    safe_paragraph = ' '.join(safe_paragraph.split())
                    safe_paragraph = safe_paragraph.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                    if safe_paragraph:
                        story.append(Paragraph(safe_paragraph, body_style))
                else:
                    story.append(Spacer(1, 6))
        
        # Создаем PDF
        doc.build(story)
        
        # Получаем байты
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info("PDF файл успешно создан в памяти")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Ошибка создания PDF файла в памяти: {e}")
        return None

def create_and_upload_pdf_to_drive(
    text: str, 
    file_name: str,
    folder_name: Optional[str] = None,
    title: str = "Документ",
    credentials_path: str = "oauth.json"
) -> Dict[str, Any]:
    """
    Создает PDF файл из текста и загружает его в Google Drive
    
    Args:
        text: Текст для записи в PDF
        file_name: Имя файла (без расширения .pdf)
        folder_name: Имя папки в Google Drive (создается если не существует)
        title: Заголовок документа
        credentials_path: Путь к файлу OAuth credentials
    
    Returns:
        Словарь с результатом операции
    """
    try:
        # Добавляем расширение .pdf если его нет
        if not file_name.endswith('.pdf'):
            file_name += '.pdf'
        
        # Создаем PDF в памяти
        pdf_bytes = create_pdf_bytes_from_text(text, title)
        if not pdf_bytes:
            return {
                'success': False,
                'error': 'Не удалось создать PDF файл'
            }
        
        # Инициализируем Google Drive Manager
        drive_manager = GoogleDriveManager(credentials_path=credentials_path)
        
        # Получаем или создаем папку
        folder_id = None
        if folder_name:
            folder_id = drive_manager.get_or_create_folder(folder_name)
            if not folder_id:
                return {
                    'success': False,
                    'error': 'Не удалось создать папку в Google Drive'
                }
        
        # Загружаем PDF файл
        upload_result = drive_manager.upload_file_from_bytes(
            file_data=pdf_bytes,
            file_name=file_name,
            mime_type='application/pdf',
            folder_id=folder_id
        )
        
        if upload_result.get('success'):
            file_id = upload_result.get('file_id')
            
            # Делаем файл общедоступным
            if file_id:
                permissions_set = drive_manager.set_file_permissions(
                    file_id, 
                    permission_type='reader', 
                    role='anyone'
                )
                if permissions_set:
                    logger.info(f"PDF файл '{file_name}' успешно загружен и сделан общедоступным")
                else:
                    logger.warning(f"PDF файл '{file_name}' загружен, но не удалось сделать его общедоступным")
            
            return upload_result
        else:
            return upload_result
            
    except Exception as e:
        logger.error(f"Ошибка создания и загрузки PDF: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def save_pdf_locally_and_upload(
    text: str,
    file_name: str,
    folder_name: Optional[str] = None,
    title: str = "Документ",
    local_dir: str = "downloads",
    credentials_path: str = "oauth.json"
) -> Dict[str, Any]:
    """
    Создает PDF файл локально и загружает его в Google Drive
    
    Args:
        text: Текст для записи в PDF
        file_name: Имя файла (без расширения .pdf)
        folder_name: Имя папки в Google Drive
        title: Заголовок документа
        local_dir: Локальная директория для сохранения
        credentials_path: Путь к файлу OAuth credentials
    
    Returns:
        Словарь с результатом операции
    """
    try:
        # Добавляем расширение .pdf если его нет
        if not file_name.endswith('.pdf'):
            file_name += '.pdf'
        
        # Создаем локальный путь
        local_path = os.path.join(local_dir, file_name)
        
        # Создаем PDF файл локально
        if not create_pdf_from_text(text, local_path, title):
            return {
                'success': False,
                'error': 'Не удалось создать PDF файл локально'
            }
        
        # Инициализируем Google Drive Manager
        drive_manager = GoogleDriveManager(credentials_path=credentials_path)
        
        # Получаем или создаем папку
        folder_id = None
        if folder_name:
            folder_id = drive_manager.get_or_create_folder(folder_name)
            if not folder_id:
                # Удаляем локальный файл в случае ошибки
                if os.path.exists(local_path):
                    os.remove(local_path)
                return {
                    'success': False,
                    'error': 'Не удалось создать папку в Google Drive'
                }
        
        # Загружаем файл
        upload_result = drive_manager.upload_file(
            file_path=local_path,
            folder_id=folder_id,
            file_name=file_name
        )
        
        if upload_result.get('success'):
            file_id = upload_result.get('file_id')
            
            # Делаем файл общедоступным
            if file_id:
                permissions_set = drive_manager.set_file_permissions(
                    file_id, 
                    permission_type='reader', 
                    role='anyone'
                )
                if permissions_set:
                    logger.info(f"PDF файл '{file_name}' успешно загружен и сделан общедоступным")
                else:
                    logger.warning(f"PDF файл '{file_name}' загружен, но не удалось сделать его общедоступным")
        
        # Удаляем локальный файл после загрузки
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Локальный файл {local_path} удален")
        
        return upload_result
        
    except Exception as e:
        logger.error(f"Ошибка создания и загрузки PDF: {e}")
        # Удаляем локальный файл в случае ошибки
        local_path = os.path.join(local_dir, file_name)
        if os.path.exists(local_path):
            os.remove(local_path)
        return {
            'success': False,
            'error': str(e)
        }
