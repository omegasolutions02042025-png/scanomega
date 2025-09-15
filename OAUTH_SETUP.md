# Настройка OAuth Client ID для Google Drive

## 1. Создание OAuth Client ID в Google Cloud Console

### Шаг 1: Создание проекта
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Запомните Project ID

### Шаг 2: Включение Google Drive API
1. В левом меню выберите "APIs & Services" → "Library"
2. Найдите "Google Drive API"
3. Нажмите "Enable"

### Шаг 3: Настройка OAuth consent screen
1. Перейдите в "APIs & Services" → "OAuth consent screen"
2. Выберите "External" (для тестирования)
3. Заполните обязательные поля:
   - App name: "Resume Scanner Bot"
   - User support email: ваш email
   - Developer contact information: ваш email
4. Нажмите "Save and Continue"
5. На странице "Scopes" нажмите "Add or Remove Scopes"
6. Найдите и добавьте:
   - `https://www.googleapis.com/auth/drive`
7. Нажмите "Save and Continue"
8. На странице "Test users" добавьте свой email
9. Нажмите "Save and Continue"

### Шаг 4: Создание OAuth Client ID
1. Перейдите в "APIs & Services" → "Credentials"
2. Нажмите "Create Credentials" → "OAuth client ID"
3. Выберите "Desktop application"
4. Введите имя: "Drive Upload Client"
5. Нажмите "Create"
6. **ВАЖНО**: Скачайте JSON файл с credentials
7. Переименуйте файл в `client_secret.json`
8. Поместите файл в корневую папку проекта

## 2. Структура файла client_secret.json

Файл должен содержать примерно такую структуру:

```json
{
  "installed": {
    "client_id": "ваш_client_id.apps.googleusercontent.com",
    "project_id": "ваш_project_id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "ваш_client_secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

## 3. Использование OAuth в коде

### Базовое использование:
```python
from google_disk import upload_file_to_drive

# Загрузка с OAuth (по умолчанию)
result = upload_file_to_drive(
    file_path="document.pdf",
    folder_name="Резюме",
    use_oauth=True,  # OAuth по умолчанию
    credentials_path="client_secret.json"
)
```

### Использование класса напрямую:
```python
from google_disk import GoogleDriveManager

# OAuth аутентификация
drive_manager = GoogleDriveManager(
    credentials_path="client_secret.json",
    use_oauth=True,
    token_file="token.pickle"
)

# Загрузка файла
result = drive_manager.upload_file("test.txt", folder_id=None)
```

## 4. Процесс первой авторизации

При первом запуске:
1. Откроется браузер с Google OAuth страницей
2. Войдите в свой Google аккаунт
3. Разрешите доступ к Google Drive
4. Токен автоматически сохранится в `token.pickle`
5. При последующих запусках авторизация не потребуется

## 5. Важные моменты

### Безопасность:
- **НЕ** добавляйте `client_secret.json` в git
- **НЕ** добавляйте `token.pickle` в git
- Добавьте в `.gitignore`:
```
client_secret.json
token.pickle
```

### Обновление токенов:
- Токены автоматически обновляются
- Если токен истек, будет запущена повторная авторизация

### Переключение между Service Account и OAuth:
```python
# OAuth (рекомендуется для личного использования)
drive_manager = GoogleDriveManager(
    credentials_path="client_secret.json",
    use_oauth=True
)

# Service Account (для серверных приложений)
drive_manager = GoogleDriveManager(
    credentials_path="credentials.json",
    use_oauth=False
)
```

## 6. Устранение проблем

### Ошибка "redirect_uri_mismatch":
- Убедитесь, что используете "Desktop application" тип
- Проверьте redirect_uris в client_secret.json

### Ошибка "access_denied":
- Проверьте настройки OAuth consent screen
- Убедитесь, что ваш email добавлен в Test users

### Ошибка "insufficient_scope":
- Проверьте, что добавлен scope `https://www.googleapis.com/auth/drive`

## 7. Тестирование

Запустите тест:
```bash
python test_google_drive.py
```

При первом запуске откроется браузер для авторизации.
