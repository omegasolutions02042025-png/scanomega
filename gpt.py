import google.generativeai as genai 
import os
import json
import re
from maps_for_sheet import (
    ROLES_MAP, GRADE_MAP, PROGRAM_LANG_MAP, FRAMEWORKS_MAP, TECH_MAP,
    PRODUCT_INDUSTRIES_MAP, LANG_MAP, PORTFOLIO_MAP, WORK_TIME_MAP,
    WORK_FORM_MAP, AVAILABILITY_MAP, CONTACTS_MAP
)


def fix_color_formatting(text: str) -> str:
    """Исправляет цветовые значения в HTML-тегах, добавляя # перед hex-кодами"""
    # Исправляем color="1F4E79" на color="#1F4E79"
    text = re.sub(r'color="([0-9A-Fa-f]{6})"', r'color="#\1"', text)
    # Исправляем color="555555" на color="#555555"
    text = re.sub(r'color="([0-9A-Fa-f]{3,6})"', r'color="#\1"', text)
    return text




def process_resume(text: str, file_name: str = "") -> dict | None:
    file_info = f"\nНазвание файла: {file_name}\n" if file_name else ""
    
    # Создаем строки с доступными значениями из всех мап
    grade_values = ', '.join(f'"{v}"' for v in GRADE_MAP.values())
    roles_values = ', '.join(f'"{v}"' for v in ROLES_MAP.values())
    prog_lang_values = ', '.join(f'"{v}"' for v in PROGRAM_LANG_MAP.values())
    frameworks_values = ', '.join(f'"{v}"' for v in FRAMEWORKS_MAP.values())
    tech_values = ', '.join(f'"{v}"' for v in TECH_MAP.values())
    industries_values = ', '.join(f'"{v}"' for v in PRODUCT_INDUSTRIES_MAP.values())
    lang_values = ', '.join(f'"{v}"' for v in LANG_MAP.values())
    portfolio_values = ', '.join(f'"{v}"' for v in PORTFOLIO_MAP.values())
    work_time_values = ', '.join(f'"{v}"' for v in WORK_TIME_MAP.values())
    work_form_values = ', '.join(f'"{v}"' for v in WORK_FORM_MAP.values())
    availability_values = ', '.join(f'"{v}"' for v in AVAILABILITY_MAP.values())
    contacts_values = ', '.join(f'"{v}"' for v in CONTACTS_MAP.values())
    
    prompt = f"""Ваша задача — извлечь указанные данные из текста резюме и представить их в формате JSON. 

ВАЖНО: НЕ ПРИДУМЫВАЙ И НЕ ДОБАВЛЯЙ ИНФОРМАЦИЮ, КОТОРОЙ НЕТ В ТЕКСТЕ РЕЗЮМЕ! 
Используй только ту информацию, которая явно указана в резюме. Если какой-то информации нет - указывай null или пустые значения.

Вот текст резюме:
{text}
{file_info}
Извлеки следующие поля:

**ОСНОВНАЯ ИНФОРМАЦИЯ:**
- Специализация (основная): `specialization` (СТРОГО в формате: 'Python Developer', 'Java Developer', 'Frontend Developer', 'Backend Developer', 'DevOps Engineer', 'Data Scientist' и т.д. Используй конкретную должность с технологией/направлением БЕЗ слов 'Разработчик')
- Имя: `firstName` (словарь с русским и английским вариантами (переведи русское в английское и наоборот): {{"На русском": "Иван", "На английском": "Ivan"}})
- Фамилия: `lastName` (словарь с русским и английским вариантами:(переведи русское в английское и наоборот) {{"На русском": "Иванов", "На английском": "Ivanov"}})
- Отчество: `patronymic` (словарь с русским и английским вариантами: (переведи русское в английское и наоборот){{"На русском": "Иванович", "На английском": "Ivanovich"}})
- Дата рождения: `dateOfBirth` (укажи в формате: '01.01.2000')
- Грейд: `grade` (словарь с найденными грейдами из доступных: {grade_values}. Формат: {{"Junior": true, "Middle": false, "Senior": true}})
- Общий опыт в IT: `totalExperience` (укажи в годах)
- Спец опыт в IT: `specialExperience` (СТРОГО в формате: 'Python Developer - 5 лет', 'Java Developer - 3 года', 'DevOps Engineer - 2 года'. Найди конкретную должность и точное количество лет опыта в этой роли)

- Дата выхода на новое место работы: `dateOfExit`

**ТЕХНИЧЕСКИЕ НАВЫКИ:**
- Языки программирования: `programmingLanguages` (словарь с найденными языками из доступных: {prog_lang_values}. Формат: {{"Python": true, "JavaScript": false, "Java": true}})
- Фреймворки: `frameworks` (словарь с найденными фреймворками из доступных: {frameworks_values}. Формат: {{"Django": true, "React": false, "Spring Boot": true}})
- Технологии: `technologies` (словарь с найденными технологиями из доступных: {tech_values}. Формат: {{"Docker": true, "PostgreSQL": false, "AWS": true}})
- Роли: `roles` (словарь с найденными ролями из доступных: {roles_values}. Формат: {{"Python Developer": true, "Frontend Developer": false, "Backend Developer": true}})

**КОНТАКТНАЯ ИНФОРМАЦИЯ:**
- Страна: `location`
- Город: `city`
- Контакты: `contacts` (словарь со всеми контактными данными: {{"phone": "+79001234567", "email": "test@example.com", "telegram": "@username", "linkedin": "https://linkedin.com/in/username", "skype": "username", "github": "https://github.com/username", "gitlab": null, "whatsapp": "+79001234567", "viber": null, "discord": "username#1234", "slack": null, "microsoftTeams": null, "zoom": null, "googleMeet": null, "facebook": null, "instagram": "@username", "twitter": "@username", "vk": "https://vk.com/username", "tiktok": null, "reddit": null, "stackoverflow": "https://stackoverflow.com/users/123456/username", "habrCareer": null}})
- Другие портфолио: `portfolio` (словарь с найденными портфолио из доступных: {portfolio_values}. Формат: {{"GitHub": true, "LinkedIn": false, "Personal Website": true}})

**ЯЗЫКИ И ПРОЕКТЫ:**
- Иностранные языки: `languages` (словарь с найденными языками из доступных: {lang_values}. Формат: {{"English": "B2", "German": "A1", "Spanish": null}})
- Отрасли проектов: `projectIndustries` (словарь с найденными отраслями из доступных: {industries_values}. Формат: {{"FinTech": true, "Healthcare": false, "E-commerce": true}})

**УСЛОВИЯ РАБОТЫ:**
- Доступность: `availability` (словарь с найденной доступностью из доступных: {availability_values}. Формат: {{"Open to offers": true, "Not looking": false, "Considering offers": true}})
- Формат работы: `workTime` (словарь с найденными форматами из доступных: {work_time_values}. Формат: {{"Full-time": true, "Part-time": false, "Contract": true}})
- Форма трудоустройства: `workForm` (словарь с найденными формами из доступных: {work_form_values}. Формат: {{"Оформление в штат": true, "B2B contract": false, "Самозанятый": true}})
- Зарплатные ожидания: `salaryExpectations` (словарь с суммой и валютой: {{"amount": "150000", "currency": "RUB"}} или {{"amount": "1100", "currency": "USD"}}. Валюты ТОЛЬКО: RUB (рубли, руб), USD (доллары, $, у.е.), EUR (евро, €), BYN (белорусские рубли). ВАЖНО: у.е. всегда означает USD. Валюту всегда пиши ЗАГЛАВНЫМИ буквами. Если не найдено в тексте резюме, обязательно проверь название файла - там могут быть указаны зарплатные ожидания в виде чисел. ВАЖНО: если в названии файла есть числа типа "от 200_000", "200000", "2500" и т.д., то считай это зарплатными ожиданиями в RUB)
- Рейт (руб): `rateRub`

Если какое-либо поле отсутствует в резюме, используй значение `null` для строк или пустой словарь `{{}}` для словарей.

**Пример JSON-структуры:**
```json
{{
  "specialization": "Python Developer",
  "firstName": {{"На русском": "Иван", "На английском": "Ivan"}},
  "lastName": {{"На русском": "Иванов", "На английском": "Ivanov"}},
  "patronymic": {{"На русском": "Иванович", "На английском": "Ivanovich"}},
  "dateOfBirth": "01.01.2000",
  "grade": {{"Senior": true, "Middle": false, "Junior": false}},
  "totalExperience": "8 лет",
  "dateOfExit": "2025-08-30",
  "specialExperience": "Python Developer - 5 лет",
  "programmingLanguages": {{"Python": true, "JavaScript": true, "TypeScript": true}},
  "frameworks": {{"Django": true, "FastAPI": true, "React": true}},
  "technologies": {{"PostgreSQL": true, "Docker": true, "AWS": true, "Redis": true}},
  "roles": {{"Python Developer": true, "Backend Developer": true}},
  "location": "Россия",
  "city": "Москва",
  "contacts": {{
    "phone": "+79001234567",
    "email": "ivan.ivanov@example.com",
    "linkedin": "https://linkedin.com/in/ivanov",
    "telegram": "@ivanov_dev",
    "skype": "ivan.ivanov",
    "github": "https://github.com/ivanov",
    "gitlab": "https://gitlab.com/ivanov",
    "whatsapp": "+79001234567",
    "viber": "+79001234567",
    "discord": "ivanov#1234",
    "slack": "@ivanov",
    "microsoftTeams": "ivan.ivanov@company.com",
    "zoom": "ivan.ivanov@company.com",
    "googleMeet": "ivan.ivanov@gmail.com",
    "facebook": "https://facebook.com/ivan.ivanov",
    "instagram": "@ivanov_dev",
    "twitter": "@ivanov_dev",
    "vk": "https://vk.com/ivanov",
    "tiktok": "@ivanov_dev",
    "reddit": "u/ivanov_dev",
    "stackoverflow": "https://stackoverflow.com/users/123456/ivanov",
    "habrCareer": "https://career.habr.com/ivanov"
  }},
  "portfolio": {{"GitHub": true, "Medium": true, "Personal Website": false}},
  "languages": {{"English": "B2", "Spanish": "A2", "German": null}},
  "projectIndustries": {{"FinTech": true, "Healthcare": true, "E-commerce": false}},
  "availability": {{"Open to offers": true, "Not looking": false}},
  "workTime": {{"Full-time": true, "Part-time": false, "Contract": false}},
  "workForm": {{"Оформление в штат": true, "B2B contract": true, "Самозанятый": false}},
  "salaryExpectations": {{"amount": "300000", "currency": "RUB"}},
  "rateRub": "1500"
}}
```"""

    genai.configure(api_key=os.getenv("GPT_KEY"))
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    response_text = response.text.strip().replace("```json", "").replace("```", "").strip()

    try:
        response_json = json.loads(response_text)
        return response_json
    except json.JSONDecodeError:
        print(f"Ошибка при разборе JSON: {response_text}")
        return None


def translate_name_to_english(russian_name: str) -> str:
    """Переводит русское имя на английский язык"""
    
    # Словарь для транслитерации русских имен
    name_translations = {
        # Мужские имена
        'александр': 'Alexander', 'алексей': 'Alexey', 'андрей': 'Andrey', 'антон': 'Anton',
        'артем': 'Artem', 'артур': 'Arthur', 'борис': 'Boris', 'вадим': 'Vadim',
        'валентин': 'Valentin', 'василий': 'Vasily', 'виктор': 'Victor', 'виталий': 'Vitaly',
        'владимир': 'Vladimir', 'владислав': 'Vladislav', 'вячеслав': 'Vyacheslav',
        'геннадий': 'Gennady', 'георгий': 'George', 'григорий': 'Gregory', 'данил': 'Danil',
        'даниил': 'Daniel', 'денис': 'Denis', 'дмитрий': 'Dmitry', 'евгений': 'Eugene',
        'егор': 'Egor', 'иван': 'Ivan', 'игорь': 'Igor', 'илья': 'Ilya',
        'кирилл': 'Kirill', 'константин': 'Konstantin', 'леонид': 'Leonid', 'максим': 'Maxim',
        'михаил': 'Mikhail', 'никита': 'Nikita', 'николай': 'Nikolay', 'олег': 'Oleg',
        'павел': 'Pavel', 'петр': 'Peter', 'роман': 'Roman', 'сергей': 'Sergey',
        'станислав': 'Stanislav', 'тимур': 'Timur', 'федор': 'Fedor', 'юрий': 'Yury',
        
        # Женские имена
        'александра': 'Alexandra', 'алина': 'Alina', 'алла': 'Alla', 'анастасия': 'Anastasia',
        'анна': 'Anna', 'валентина': 'Valentina', 'валерия': 'Valeria', 'вера': 'Vera',
        'виктория': 'Victoria', 'галина': 'Galina', 'дарья': 'Darya', 'екатерина': 'Ekaterina',
        'елена': 'Elena', 'елизавета': 'Elizaveta', 'жанна': 'Zhanna', 'ирина': 'Irina',
        'карина': 'Karina', 'кристина': 'Kristina', 'лариса': 'Larisa', 'людмила': 'Lyudmila',
        'марина': 'Marina', 'мария': 'Maria', 'наталья': 'Natalya', 'ольга': 'Olga',
        'полина': 'Polina', 'светлана': 'Svetlana', 'татьяна': 'Tatyana', 'юлия': 'Julia'
    }
    
    # Транслитерация фамилий и отчеств
    transliteration_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    
    name_lower = russian_name.lower().strip()
    
    # Проверяем, есть ли имя в словаре переводов
    if name_lower in name_translations:
        return name_translations[name_lower]
    
    # Если нет в словаре, используем транслитерацию
    result = ''
    for char in name_lower:
        if char in transliteration_map:
            result += transliteration_map[char]
        else:
            result += char
    
    # Делаем первую букву заглавной
    return result.capitalize()


def create_new_resume(text, id):
  
  prompt  = f"""PROMPT: Expert Resume Formatter 🧠 Роль: Эксперт по форматированию и унификации резюме 

Ты — профессиональный специалист по оформлению и стандартизации резюме, обладающий опытом работы с международными IT-компаниями и HR-платформами. 
Твоя задача: взять любое резюме кандидата (на русском или английском языке) и преобразовать его в строго структурированное и визуально выверенное резюме, соответствующее корпоративному стилю.

⚠️ КРИТИЧЕСКИ ВАЖНО: НЕ ПРИДУМЫВАЙ И НЕ ДОБАВЛЯЙ ИНФОРМАЦИЮ, КОТОРОЙ НЕТ В ИСХОДНОМ РЕЗЮМЕ!
- Используй только ту информацию, которая есть в тексте резюме
- Не добавляй технологии, навыки, опыт работы или другие данные от себя
- Если какой-то информации нет в резюме - не включай эту секцию
- Переформатируй и структурируй только существующую информацию 

🎯 Цель: 

Создать аккуратно оформленное, двуязычное резюме, удобное для восприятия заказчиком (включая технических менеджеров и HR), в формате, пригодном для PDF, Word и печати. 

🎨 ВИЗУАЛЬНЫЙ СТИЛЬ ОФОРМЛЕНИЯ:

При создании резюме используй следующую цветовую схему и стили:
• Фон: Белый #FFFFFF  
• Основной текст: Чёрный #000000  
• Второстепенный текст: Серый #555555 (даты, города, названия компаний)  
• Заголовки секций: Голубой #4A90E2, ЗАГЛАВНЫМИ  
• Подзаголовки: Чёрный/тёмно-серый #333333  
• Акценты (технологии): Чёрный #000000, обычный шрифт  
• Разделители: Светло-серый #DDDDDD (лучше использовать отступы)  

ВАЖНО: В тексте резюме используй HTML-теги для стилизации:  
- <b color="#4A90E2">ЗАГОЛОВКИ СЕКЦИЙ</b> — голубой цвет, ЗАГЛАВНЫМИ  
- <font color="#555555">Второстепенный текст</font> — серый  
- Технологии — обычным чёрным шрифтом  

✅ ЧТО ДОЛЖНО БЫТЬ СДЕЛАНО 

1. 🔐 Анонимизация:  

Удалить:  
• Фамилию  
• Отчество  
• Телефон, email, Skype и другие контакты  
• Ссылки на соцсети (LinkedIn, GitHub и т.д.)  
• Адрес проживания (город и страна остаются)  
• Упоминания зарплатных ожиданий  

Оставить только:  
• Имя  
• ID кандидата в формате Имя (ID-{id})  

2. 📑 Обязательная структура финального резюме:  

Добавляй только те блоки, где есть содержимое.  

**ДЛЯ РУССКОЙ ВЕРСИИ:**  
<b color="#4A90E2">ИНФОРМАЦИЯ О КАНДИДАТЕ</b>  
<b color="#4A90E2">РЕЗЮМЕ</b>  
<b color="#4A90E2">НАВЫКИ</b>  
<b color="#4A90E2">ОПЫТ РАБОТЫ</b>  
<b color="#4A90E2">ОБРАЗОВАНИЕ</b>  
<b color="#4A90E2">СЕРТИФИКАТЫ</b>  
<b color="#4A90E2">ДОПОЛНИТЕЛЬНО</b>  

**ДЛЯ АНГЛИЙСКОЙ ВЕРСИИ:**  
<b color="#4A90E2">CANDIDATE INFO</b>  
<b color="#4A90E2">SUMMARY</b>  
<b color="#4A90E2">SKILLS</b>  
<b color="#4A90E2">WORK EXPERIENCE</b>  
<b color="#4A90E2">EDUCATION</b>  
<b color="#4A90E2">CERTIFICATIONS</b>  
<b color="#4A90E2">ADDITIONAL INFORMATION</b>  

ВСЕ ЗАГОЛОВКИ СЕКЦИЙ ДОЛЖНЫ БЫТЬ СИНИМИ (#4A90E2) И ЗАГЛАВНЫМИ БУКВАМИ!  

3. 🧠 Стандарты для каждого блока:  

📌 Информация о кандидате (русская версия):  

<b color="#4A90E2">ИНФОРМАЦИЯ О КАНДИДАТЕ</b>  

Имя (ID-{id})  
Грейд и специализация: Senior Salesforce Developer и т.д.  
Если должность размытая → Software Engineer (specialization not specified) — [Apex, SOQL, LWC]  
Локация: Минск, Беларусь, Remote и т.д.  

📌 Candidate Info (английская версия):  

<b color="#4A90E2">CANDIDATE INFO</b>  

English name (ID-{id}) — только английское имя!  
Grade and Specialization: Senior Salesforce Developer и т.д.  
If unclear → Software Engineer (specialization not specified) — [Apex, SOQL, LWC]  
Location: Minsk, Belarus, Remote и т.д.  

📌 Резюме (русская версия):  

<b color="#4A90E2">РЕЗЮМЕ</b>  

Абзац: опыт, ключевые технологии, специализация, сертификации, проекты.  

📌 Summary (английская версия):  

<b color="#4A90E2">SUMMARY</b>  

Paragraph: total experience, technologies, specialization, certifications, projects.  

📌 Навыки (русская версия):  

<b color="#4A90E2">НАВЫКИ</b>  

Языки и платформы: Apex, JavaScript, SOQL  
UI и фреймворки: LWC, Aura, SLDS  
Интеграции: REST, SOAP, Webhooks  
Инструменты: VS Code, Git, Jira  
CI/CD и DevOps: (если есть)  

📌 Skills (английская версия):  

<b color="#4A90E2">SKILLS</b>  

Languages & Platforms: Apex, JavaScript, SOQL  
UI & Frameworks: LWC, Aura, SLDS  
Integrations: REST, SOAP, Webhooks  
Tools: VS Code, Git, Jira  
CI/CD, Testing, DevOps: (if any)  

📌 Опыт работы (русская версия):  

<b color="#4A90E2">ОПЫТ РАБОТЫ</b>  

Должность — Компания  
<font color="#555555">Сроки | Локация</font>  
Описание проекта: (1–2 предложения)  
Отрасль: FinTech, Healthcare и т.д.  
Задачи и достижения: список  
Технологии: перечисли  

📌 Work Experience (английская версия):  

<b color="#4A90E2">WORK EXPERIENCE</b>  

Position — Company  
<font color="#555555">Period | Location</font>  
Project Description: (1–2 sentences)  
Industry: FinTech, Healthcare и т.д.  
Tasks and Achievements: bulleted list  
Technologies: list  

📌 Образование (русская версия):  

<b color="#4A90E2">ОБРАЗОВАНИЕ</b>  

Уровень, специальность, университет, страна, год  

📌 Education (английская версия):  

<b color="#4A90E2">EDUCATION</b>  

Level, specialty, university, country, year  

📌 Сертификаты (русская версия):  

<b color="#4A90E2">СЕРТИФИКАТЫ</b>  

Список с датами  

📌 Certifications (английская версия):  

<b color="#4A90E2">CERTIFICATIONS</b>  

List with dates  

📌 Дополнительно (русская версия):  

<b color="#4A90E2">ДОПОЛНИТЕЛЬНО</b>  

📌 Additional Information (английская версия):  

<b color="#4A90E2">ADDITIONAL INFORMATION</b>  

Languages: (с уровнями)  
Additional tools: open-source, mentoring, volunteering  

🌐 Перевод:  
Если резюме на русском → добавь английскую версию.  
Если резюме на английском → добавь русскую.  
В английской версии ни одного русского символа!  

ВАЖНО: Верни результат СТРОГО в формате JSON:
{{
  "russian": "полный текст резюме на русском языке с HTML-тегами для стилизации",
  "english": "полный текст резюме на английском языке с HTML-тегами для стилизации"
}}

Текст резюме: {text}

"""



  genai.configure(api_key=os.getenv("GPT_KEY"))
  model = genai.GenerativeModel("gemini-2.5-flash")
  response = model.generate_content(prompt)
  response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
  
  try:
    response_json = json.loads(response_text)
    
    # Исправляем цветовые значения в HTML-тегах
    if "russian" in response_json:
      response_json["russian"] = fix_color_formatting(response_json["russian"])
    if "english" in response_json:
      response_json["english"] = fix_color_formatting(response_json["english"])
      
      # Переводим русские имена на английский в английской версии
      english_text = response_json["english"]
      
      # Ищем русские имена в тексте и заменяем их на английские
      import re
      
      # Расширенный паттерн для поиска русских имен, фамилий и отчеств (кириллица)
      russian_name_pattern = r'\b[А-ЯЁ][а-яё]{1,}(?:\s+[А-ЯЁ][а-яё]{1,})*\b'
      
      def replace_russian_names(match):
        russian_name = match.group(0)
        # Если это составное имя (имя + фамилия), переводим каждую часть
        if ' ' in russian_name:
          parts = russian_name.split()
          english_parts = [translate_name_to_english(part) for part in parts]
          return ' '.join(english_parts)
        else:
          return translate_name_to_english(russian_name)
      
      # Заменяем все найденные русские имена на английские
      english_text = re.sub(russian_name_pattern, replace_russian_names, english_text)
      
      response_json["english"] = english_text
    
    return response_json
  except json.JSONDecodeError:
    print(f"Ошибка при разборе JSON ответа create_new_resume: {response_text}")
    # Возвращаем fallback структуру с исправленными цветами
    fixed_text = fix_color_formatting(response_text)
    return {
      "russian": fixed_text,
      "english": fixed_text
    }
