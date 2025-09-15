# Настройка Google Sheets API

## Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API и Google Drive API:
   - Перейдите в "APIs & Services" > "Library"
   - Найдите и включите "Google Sheets API"
   - Найдите и включите "Google Drive API"

## Шаг 2: Создание Service Account

1. Перейдите в "APIs & Services" > "Credentials"
2. Нажмите "Create Credentials" > "Service Account"
3. Заполните информацию о service account
4. Нажмите "Create and Continue"
5. Добавьте роль "Editor" для доступа к Google Sheets
6. Нажмите "Done"

## Шаг 3: Создание ключа

1. В списке Service Accounts найдите созданный аккаунт
2. Нажмите на него и перейдите во вкладку "Keys"
3. Нажмите "Add Key" > "Create New Key"
4. Выберите формат JSON и нажмите "Create"
5. Файл с ключом будет скачан на ваш компьютер

## Шаг 4: Настройка переменных окружения

### Вариант 1: Использование JSON файла
1. Переместите скачанный JSON файл в папку проекта
2. Переименуйте его в `credentials.json`

### Вариант 2: Использование переменной окружения (рекомендуется)
1. Откройте скачанный JSON файл
2. Скопируйте весь содержимое файла
3. Добавьте в файл `.env` строку:
```
GOOGLE_CREDENTIALS_JSON={"type": "service_account", "project_id": "your-project-id", ...}
```

## Шаг 5: Предоставление доступа к таблице

1. Из JSON файла скопируйте email service account (поле "client_email")
2. Откройте Google Sheets где хотите сохранять данные
3. Нажмите "Share" и добавьте email service account с правами "Editor"

## Пример использования

```python
from google_sheet import add_resume_to_sheet, get_sheet_url

# Данные резюме (из process_resume)
resume_data = {
    "specialization": "Backend-разработчик",
    "firstName": "Иван",
    "lastName": "Иванов",
    # ... остальные поля
}

# Добавить в Google таблицу
success = add_resume_to_sheet(resume_data)
if success:
    print("Резюме добавлено успешно!")
    url = get_sheet_url()
    print(f"URL таблицы: {url}")
```

## Функции модуля google_sheet.py

- `add_resume_to_sheet(resume_data, sheet_name)` - добавить резюме в таблицу
- `get_sheet_url(sheet_name)` - получить URL таблицы  
- `search_resume_by_field(field_name, search_value, sheet_name)` - поиск по полю
- `create_or_get_sheet(sheet_name)` - создать или получить таблицу

## Структура таблицы

Таблица автоматически создается со следующими столбцами:
- Дата добавления
- Специализация
- Фамилия, Имя, Отчество
- Грейд
- Стэк технологий
- Отрасль проекта
- Спец опыт
- Общий опыт
- Уровень английского
- Доступность
- Локация
- Контакты (LinkedIn, Telegram, Телефон, E-mail)
- Зарплатные ожидания
- Рейт (руб)
