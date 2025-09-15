import os
import io
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import mimetypes
from typing import Optional, Dict, Any
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDriveManager:
    """Класс для работы с Google Drive API через OAuth аутентификацию"""
    
    def __init__(self, credentials_path: str = "oauth.json", token_file: str = "token.pickle"):
        """
        Инициализация менеджера Google Drive
        
        Args:
            credentials_path: Путь к файлу с OAuth учетными данными (client_secret.json)
            token_file: Путь к файлу с сохраненным OAuth токеном
        """
        self.credentials_path = credentials_path
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """OAuth аутентификация в Google Drive API"""
        try:
            # Области доступа для Google Drive
            SCOPES = ['https://www.googleapis.com/auth/drive']
            credentials = None
            
            logger.info("Использование OAuth аутентификации")
            
            # Проверяем существующий токен
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    credentials = pickle.load(token)
            
            # Если нет действительных учетных данных, запускаем поток авторизации
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    logger.info("Обновление истекшего токена")
                    credentials.refresh(Request())
                else:
                    logger.info("Запуск потока OAuth авторизации")
                    if not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(f"Файл OAuth credentials не найден: {self.credentials_path}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    credentials = flow.run_local_server(port=0)
                
                # Сохраняем учетные данные для следующего запуска
                with open(self.token_file, 'wb') as token:
                    pickle.dump(credentials, token)
            
            logger.info("OAuth аутентификация успешна")
            
            # Создание сервиса Google Drive
            self.service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Drive сервис успешно инициализирован")
            
        except Exception as e:
            logger.error(f"Ошибка OAuth аутентификации Google Drive: {e}")
            raise
    
    def upload_file(self, file_path: str, folder_id: Optional[str] = None, 
                   file_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Загрузка файла в Google Drive
        
        Args:
            file_path: Путь к загружаемому файлу
            folder_id: ID папки в Google Drive (если None, загружается в корень)
            file_name: Имя файла в Google Drive (если None, используется оригинальное имя)
        
        Returns:
            Словарь с информацией о загруженном файле
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            
            # Определение имени файла
            if file_name is None:
                file_name = os.path.basename(file_path)
            
            # Определение MIME типа
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            # Метаданные файла
            file_metadata = {
                'name': file_name
            }
            
            # Если указана папка, добавляем её в родители
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Создание медиа объекта для загрузки
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            # Загрузка файла
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,size,createdTime'
            ).execute()
            
            logger.info(f"Файл '{file_name}' успешно загружен в Google Drive")
            logger.info(f"ID файла: {file.get('id')}")
            logger.info(f"Ссылка: {file.get('webViewLink')}")
            
            return {
                'success': True,
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'web_link': file.get('webViewLink'),
                'size': file.get('size'),
                'created_time': file.get('createdTime')
            }
            
        except Exception as e:
            logger.error(f"Ошибка загрузки файла: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_file_from_bytes(self, file_data: bytes, file_name: str, 
                              mime_type: str = 'application/octet-stream',
                              folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Загрузка файла из байтов в Google Drive
        
        Args:
            file_data: Данные файла в виде байтов
            file_name: Имя файла в Google Drive
            mime_type: MIME тип файла
            folder_id: ID папки в Google Drive
        
        Returns:
            Словарь с информацией о загруженном файле
        """
        try:
            # Метаданные файла
            file_metadata = {
                'name': file_name
            }
            
            # Если указана папка, добавляем её в родители
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Создание медиа объекта из байтов
            file_stream = io.BytesIO(file_data)
            media = MediaIoBaseUpload(file_stream, mimetype=mime_type, resumable=True)
            
            # Загрузка файла
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,size,createdTime'
            ).execute()
            
            logger.info(f"Файл '{file_name}' успешно загружен из байтов в Google Drive")
            
            return {
                'success': True,
                'file_id': file.get('id'),
                'file_name': file.get('name'),
                'web_link': file.get('webViewLink'),
                'size': file.get('size'),
                'created_time': file.get('createdTime')
            }
            
        except Exception as e:
            logger.error(f"Ошибка загрузки файла из байтов: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Создание папки в Google Drive
        
        Args:
            folder_name: Имя создаваемой папки
            parent_folder_id: ID родительской папки (если None, создается в корне)
        
        Returns:
            Словарь с информацией о созданной папке
        """
        try:
            # Метаданные папки
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            # Если указана родительская папка
            if parent_folder_id:
                folder_metadata['parents'] = [parent_folder_id]
            
            # Создание папки
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            logger.info(f"Папка '{folder_name}' успешно создана в Google Drive")
            logger.info(f"ID папки: {folder.get('id')}")
            
            return {
                'success': True,
                'folder_id': folder.get('id'),
                'folder_name': folder.get('name'),
                'web_link': folder.get('webViewLink')
            }
            
        except Exception as e:
            logger.error(f"Ошибка создания папки: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def find_folder_by_name(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Поиск папки по имени
        
        Args:
            folder_name: Имя искомой папки
            parent_folder_id: ID родительской папки для поиска
        
        Returns:
            ID найденной папки или None
        """
        try:
            # Формирование запроса поиска
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            
            # Поиск папки
            results = self.service.files().list(
                q=query,
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            if files:
                folder_id = files[0]['id']
                logger.info(f"Папка '{folder_name}' найдена с ID: {folder_id}")
                return folder_id
            else:
                logger.info(f"Папка '{folder_name}' не найдена")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка поиска папки: {e}")
            return None
    
    def get_or_create_folder(self, folder_name: str, parent_folder_id: Optional[str] = None) -> Optional[str]:
        """
        Получение ID существующей папки или создание новой
        
        Args:
            folder_name: Имя папки
            parent_folder_id: ID родительской папки
        
        Returns:
            ID папки или None в случае ошибки
        """
        # Сначала пытаемся найти существующую папку
        folder_id = self.find_folder_by_name(folder_name, parent_folder_id)
        
        if folder_id:
            return folder_id
        
        # Если папка не найдена, создаем новую
        result = self.create_folder(folder_name, parent_folder_id)
        if result['success']:
            return result['folder_id']
        
        return None
    
    def set_file_permissions(self, file_id: str, permission_type: str = 'reader', 
                           role: str = 'anyone') -> bool:
        """
        Установка разрешений для файла
        
        Args:
            file_id: ID файла
            permission_type: Тип разрешения ('reader', 'writer', 'commenter')
            role: Роль ('anyone', 'user', 'group', 'domain')
        
        Returns:
            True если разрешения установлены успешно
        """
        try:
            permission = {
                'type': role,
                'role': permission_type
            }
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            logger.info(f"Разрешения для файла {file_id} установлены успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка установки разрешений: {e}")
            return False


# Функции-обертки для удобного использования
def upload_file_to_drive(file_path: str, folder_name: Optional[str] = None, 
                        file_name: Optional[str] = None,
                        credentials_path: str = "oauth.json") -> Dict[str, Any]:
    """
    Простая функция для загрузки файла в Google Drive через OAuth
    
    Args:
        file_path: Путь к файлу
        folder_name: Имя папки в Google Drive (создается если не существует)
        file_name: Имя файла в Google Drive
        credentials_path: Путь к файлу OAuth credentials
    
    Returns:
        Результат загрузки
    """
    try:
        drive_manager = GoogleDriveManager(credentials_path=credentials_path)
        
        folder_id = None
        if folder_name:
            folder_id = drive_manager.get_or_create_folder(folder_name)
        
        return drive_manager.upload_file(file_path, folder_id, file_name)
        
    except Exception as e:
        logger.error(f"Ошибка в upload_file_to_drive: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def upload_bytes_to_drive(file_data: bytes, file_name: str, folder_name: Optional[str] = None,
                         mime_type: str = 'application/octet-stream',
                         credentials_path: str = "oauth.json") -> Dict[str, Any]:
    """
    Простая функция для загрузки данных из байтов в Google Drive через OAuth
    
    Args:
        file_data: Данные файла в байтах
        file_name: Имя файла
        folder_name: Имя папки в Google Drive
        mime_type: MIME тип файла
        credentials_path: Путь к файлу OAuth credentials
    
    Returns:
        Результат загрузки
    """
    try:
        drive_manager = GoogleDriveManager(credentials_path=credentials_path)
        
        folder_id = None
        if folder_name:
            folder_id = drive_manager.get_or_create_folder(folder_name)
        
        return drive_manager.upload_file_from_bytes(file_data, file_name, mime_type, folder_id)
        
    except Exception as e:
        logger.error(f"Ошибка в upload_bytes_to_drive: {e}")
        return {
            'success': False,
            'error': str(e)
        }