from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot
import os
from dotenv import load_dotenv
from aiogram import types
from aiogram.fsm.context import FSMContext
import json
import asyncio
from funcs import *
from kb import *
from gpt import process_resume, create_new_resume, fix_color_formatting
from google_sheet import *
from teleton_client import search_id 
from google_disk import GoogleDriveManager
from maps_for_sheet import *
from docx_generator import create_and_upload_docx_to_drive, save_docx_locally_and_upload

load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
scan_router = Router()
gm = GoogleDriveManager(credentials_path="oauth.json")
ADMIN_ID = int(os.getenv('ADMIN_ID'))

class Scan(StatesGroup):
    waiting_for_resume = State()
    confirm_add_more = State()
    processing_files = State() # Новый стейт для блокировки во время обработки

class DeleteRecord(StatesGroup):
    waiting_for_id = State()


@scan_router.callback_query(F.data == 'scan')
async def send_welcome(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    #await callback.message.answer("Отправьте id вакансии в формате 🆔XX-xxxx или 🆔xxxx")
    await callback.message.answer("Отправьте резюме в формате PDF/DOCX/RTF/TXT")
    await state.set_state(Scan.waiting_for_resume)


# @scan_router.message(Scan.waiting_for_id)
# async def send_welcome(message: types.Message, state: FSMContext):
#     id = message.text
#     vacancy_text = await search_id(id, client)
#     if isinstance(vacancy_text, Exception):
#         await message.answer("❌ Ошибка при поиске резюме!")
#     elif vacancy_text:
#         await message.answer(f'Вакансия с ID {id} найдена!')
#         await message.answer("Отправьте резюме в формате pdf/docx")
#         await state.update_data(vacancy_text=vacancy_text)
#         await state.set_state(Scan.waiting_for_resume)
#     else:
#         await message.answer(f"❌ Резюме с ID {id} не найдено!")
        


@scan_router.message(F.document, Scan.waiting_for_resume)
async def handle_document(message: types.Message, state: FSMContext):
    """Ловим документ и сохраняем его"""
    await save_document(message, state)


async def save_document(message: types.Message, state: FSMContext):
    document = message.document
    if not document:
        await message.answer("Отправьте резюме в формате PDF/DOCX/RTF/TXT")
        return

    file_info = await bot.get_file(document.file_id)
    file_path = file_info.file_path
    file_name = document.file_name

    os.makedirs("downloads", exist_ok=True)
    local_file_path = os.path.join("downloads", file_name)
    await bot.download_file(file_path, destination=local_file_path)

    

    # --- Обработка media_group_id ---
    data = await state.get_data()
    if message.media_group_id:
        if data.get("last_media_group_id") != message.media_group_id:
            # Сохраняем media_group_id и спрашиваем только один раз
            await state.update_data(last_media_group_id=message.media_group_id)
            await message.answer(f"📥 Файлы сохранены.")
            await message.answer("Хотите добавить ещё файлы?", reply_markup=get_yes_no_kb())
            await state.set_state(Scan.confirm_add_more)
    else:
        # Для одиночного файла
        await message.answer(f"📥 Файл сохранён.")
        await message.answer("Хотите добавить ещё файлы?", reply_markup=get_yes_no_kb())
        await state.set_state(Scan.confirm_add_more)


# --- Кнопка «Да» ---
@scan_router.callback_query(F.data == "add_more_yes")
async def cb_add_more_yes(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(Scan.waiting_for_resume)
    await callback.message.answer("📤 Отправьте ещё резюме.")
    await callback.answer()


# --- Кнопка «Нет» ---
@scan_router.callback_query(F.data == "add_more_no")
async def cb_add_more_no(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await start_processing(callback.message, state, callback.from_user.username)


async def start_processing(message: types.Message, state: FSMContext, rekruter_username: str):
    folder = "downloads"
    os.makedirs(folder, exist_ok=True)
    files = os.listdir(folder)

    if not files:
        await message.answer("⚠️ В папке нет файлов для обработки.")
        return

    await state.set_state(Scan.processing_files)
    await message.answer(f"🤖 Найдено {len(files)} резюме. Начинаю обработку...")
    for file_name in files:
        local_file_path = os.path.join(folder, file_name)
        try:
            await process_single_resume_from_disk(message, local_file_path, file_name, rekruter_username)
        except Exception as e:
            await message.answer(f"❌ Ошибка при обработке {file_name}: {str(e)}")
        finally:
            # Безопасное удаление файла
            if os.path.exists(local_file_path):
                os.remove(local_file_path)

    await message.answer("✅ Обработка завершена.")
    await state.set_state(Scan.waiting_for_resume)



async def process_single_resume_from_disk(message: types.Message, local_file_path: str, file_name: str, rekruter_username: str):
    resume_id = generate_random_id()
    ext = file_name.split(".")[-1].lower()

    if ext == "pdf":
        text = await process_pdf(local_file_path)
        
        await message.answer(f"✅ PDF принят и обработан\n\n Обрабатываю текст...")
    elif ext == "docx":
        text = await process_docx(local_file_path)
        
        await message.answer(f"✅ DOCX принят и обработан\n\n Обрабатываю текст...")
    elif ext == "rtf":
        text = await process_rtf(local_file_path)
        
        await message.answer(f"✅ RTF принят и обработан\n\n Обрабатываю текст...")
    elif ext == "txt":
        text = await process_txt(local_file_path)
        
        await message.answer(f"✅ TXT принят и обработан\n\n Обрабатываю текст...")
    else:
        await message.answer("❌ Поддерживаются только PDF, DOCX, RTF и TXT файлы")
        return
    
    
    user_id = message.from_user.id
    
    resume_data = process_resume(text, file_name)
    if not resume_data:
        message.answer('Не удалось извлечь данные')
        return
    first_name = resume_data.get("firstName", {}).get('ru') if resume_data.get("firstName") else None
    first_name_en = resume_data.get("firstName", {}).get('en') if resume_data.get("firstName") else None
    last_name = resume_data.get("lastName", {}).get('ru') if resume_data.get("lastName") else None
    last_name_en = resume_data.get("lastName", {}).get('en') if resume_data.get("lastName") else None
    patronymic = resume_data.get("patronymic", {}).get('ru') if resume_data.get("patronymic") else None
    patronymic_en = resume_data.get("patronymic", {}).get('en') if resume_data.get("patronymic") else None
    date_of_birth = resume_data.get("dateOfBirth")
    languages = resume_data.get("languages")
    if first_name is None and first_name_en is None:
        await message.answer("❌ В резюме нет имени. Пожалуйста уточните его")
        return
    if last_name is None and last_name_en is None:
        await message.answer("❌ В резюме нет фамилии. Пожалуйста уточните его")
        return
    if patronymic is None:
        await message.answer("❌ В резюме нет отчества. Пожалуйста уточните его")
        
    if date_of_birth is None:
        await message.answer("❌ В резюме нет даты рождения. Пожалуйста уточните его")
        
        
    # Проверяем наличие языков
    if languages is None or not languages or all(not v for v in languages.values() if isinstance(v, (str, bool))):
        await message.answer("❌ В резюме нет сведений об языках. Пожалуйста уточните сведения об языках")
        
    is_duplicate = None
    # Проверяем на дубликаты по ФИ
    if first_name and last_name:
        is_duplicate = check_duplicate_by_fio(first_name, last_name)
    elif first_name_en and last_name_en:
        is_duplicate = check_duplicate_by_fio(first_name_en, last_name_en)
    
    if is_duplicate:
        await message.answer(f"⚠️ Кандидат {last_name} {first_name} уже существует в базе данных!")
        return
    
    new_resume_data = create_new_resume(text, resume_id)
    
    # Очищаем markdown символы из обеих версий и исправляем цветовые значения
    if isinstance(new_resume_data, dict):
        new_resume_russian = new_resume_data.get('russian', '')
        new_resume_english = new_resume_data.get('english', '')
        
        # Более аккуратная очистка markdown без повреждения кириллицы
        import re
        new_resume_russian = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', new_resume_russian)
        new_resume_russian = re.sub(r'#{1,6}\s*', '', new_resume_russian)
        new_resume_english = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', new_resume_english)
        new_resume_english = re.sub(r'#{1,6}\s*', '', new_resume_english)
        
        # Исправляем цветовые значения и убираем проблемные символы
        new_resume_russian = fix_color_formatting(new_resume_russian)
        new_resume_english = fix_color_formatting(new_resume_english)
        
        # Убираем символы ■ и другие проблемные символы
        new_resume_russian = new_resume_russian.replace('■', '').replace('\ufffd', '').replace('\u25a0', '')
        new_resume_english = new_resume_english.replace('■', '').replace('\ufffd', '').replace('\u25a0', '')
    else:
        # Fallback для старого формата
        new_resume_russian = str(new_resume_data)
        new_resume_english = new_resume_russian
        
        # Более аккуратная очистка markdown
        import re
        new_resume_russian = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', new_resume_russian)
        new_resume_russian = re.sub(r'#{1,6}\s*', '', new_resume_russian)
        new_resume_english = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', new_resume_english)
        new_resume_english = re.sub(r'#{1,6}\s*', '', new_resume_english)
        
        # Исправляем цветовые значения и убираем проблемные символы
        new_resume_russian = fix_color_formatting(new_resume_russian)
        new_resume_english = fix_color_formatting(new_resume_english)
        
        # Убираем символы ■ и другие проблемные символы
        new_resume_russian = new_resume_russian.replace('■', '').replace('\ufffd', '').replace('\u25a0', '')
        new_resume_english = new_resume_english.replace('■', '').replace('\ufffd', '').replace('\u25a0', '')
    if not resume_data:
        await message.answer("❌ Не удалось извлечь данные из резюме")
        return
    
    await message.answer(f"✅ Данные извлечены!")
    
    
    
    first = resume_data.get("firstName" or {}).get('ru') or None
    last = resume_data.get("lastName" or {}).get('ru') or None
    first_en = resume_data.get("firstName" or {}).get('en') or None
    last_en = resume_data.get("lastName" or {}).get('en') or None
    

    if first and last:
        folder_name = f"{resume_id}\n{first} {last}"
    elif first:
        folder_name = f"{resume_id}\n{first}"
    elif last:
        folder_name = f"{resume_id}\n{last}"
    else:
        folder_name = f"{resume_id}\nРезюме"
    
    # Получаем или создаем папку
    folder_id = gm.get_or_create_folder(folder_name)
    if not folder_id:
        await message.answer("❌ Не удалось отправить в Google Drive")
        return
    # Загружаем файл и получаем результат с информацией о файле
    upload_result = gm.upload_file(
        file_path=local_file_path,
        folder_id=folder_id,
        file_name=file_name,
    )
    
    if upload_result.get('success'):
        file_id = upload_result.get('file_id')
        file_url = upload_result.get('web_link')
        
        # Делаем файл общедоступным
        if file_id:
            permissions_set = gm.set_file_permissions(file_id, permission_type='reader', role='anyone')
            if permissions_set:
                print(f"✅ Файл успешно загружен в Google Drive и сделан общедоступным!\n🔗")
            else:
                print(f"✅ Файл загружен в Google Drive, но не удалось сделать его общедоступным\n🔗")
        elif file_url:
            print(f"✅ Файл успешно загружен в Google Drive!\n🔗")
        else:
            print(f"✅ Файл успешно загружен в Google Drive!")
    else:
        await message.answer(f"❌ Не удалось загрузить файл в Google Drive: {upload_result.get('error', 'Неизвестная ошибка')}")
    
    # Загружаем обработанные резюме как Word документы (русская и английская версии)
    new_resume_url_russian = None
    new_resume_url_english = None
    
    if new_resume_russian:
        # Загружаем русскую версию
        new_resume_filename_ru = f"Обработанное_RU_{file_name.replace('.pdf', '').replace('.docx', '')}"
        new_resume_title_ru = f"{first} {last}" if first and last else "Резюме (RU)"
        print(new_resume_russian)
        
        docx_upload_result_ru = create_and_upload_docx_to_drive(
            text=new_resume_russian,
            file_name=new_resume_filename_ru,
            folder_name=folder_name,
            title=new_resume_title_ru,
            credentials_path="oauth.json"
        )
        
        if docx_upload_result_ru.get('success'):
            new_resume_url_russian = docx_upload_result_ru.get('web_link')
            print(f"✅ Русское резюме загружено в Word!\n🔗")
        else:
            await message.answer(f"⚠️ Не удалось загрузить русское резюме: {docx_upload_result_ru.get('error', 'Неизвестная ошибка')}")
    
    if new_resume_english:
        # Загружаем английскую версию
        new_resume_filename_en = f"Обработанное_EN_{file_name.replace('.pdf', '').replace('.docx', '')}"
        new_resume_title_en = f"{first_en} {last_en}" if first_en and last_en else "Resume (EN)"
        print(new_resume_english)
        docx_upload_result_en = create_and_upload_docx_to_drive(
            text=new_resume_english,
            file_name=new_resume_filename_en,
            folder_name=folder_name,
            title=new_resume_title_en,
            credentials_path="oauth.json"
        )
        
        if docx_upload_result_en.get('success'):
            new_resume_url_english = docx_upload_result_en.get('web_link')
            print(f"✅ Английское резюме загружено в Word!\n🔗")
        else:
            await message.answer(f"⚠️ Не удалось загрузить английское резюме: {docx_upload_result_en.get('error', 'Неизвестная ошибка')}")
    
    # Добавляем данные в Google таблицу
    
    rate_sng_for_main_table = None
    rate_eur_for_main_table = None
    salary_expectations = None
    
    salary = resume_data.get("salaryExpectations")
    salaru = salary.get('amount') if salary else None
    salary_valuta = salary.get('currency') if salary else None
    
    if salaru and salary_valuta:
        
        salary_expectations = salary.get('amount') + " " + salary.get('currency')
        
        salaru = int(salaru)
        if salary_valuta == "RUB":
            search_col = "B"
        elif salary_valuta == "BYN":
            search_col = "E"
        elif salary_valuta == "USD":
            search_col = "C"
        elif salary_valuta == "EUR":
            search_col = "D"
        
        
            
        contract_data_sng = search_and_extract_values(search_col, salaru, ["M",'N','O','P'], "Расчет ставки (штат/контракт) СНГ")
        ip_data_sng = search_and_extract_values(search_col, salaru, ["M",'N','O','P'], "Расчет ставки (ИП) СНГ")
        samozanyatii_data_sng = search_and_extract_values(search_col, salaru, ["M",'N','O','P'], "Расчет ставки (Самозанятый) СНГ")
            
        
        contract_data_es = search_and_extract_values(search_col, salaru, ['M','N','O', 'P'], "Расчет ставки (штат/контракт) ЕС/США")
        ip_data_es = search_and_extract_values(search_col, salaru, ["M",'N','O','P'], "Расчет ставки (ИП) ЕС/США")
        samozanyatii_data_es = search_and_extract_values(search_col, salaru, ["M",'N','O','P'], "Расчет ставки (Самозанятый) ЕС/США")
        print(contract_data_es)
        print(ip_data_es)
        print(samozanyatii_data_es)
        print(contract_data_sng)
        print(ip_data_sng)
        print(samozanyatii_data_sng)
    try:
        data_for_sng_rate_sheet = {
            'id' : resume_id,
            'contract_data_sng_eur': contract_data_sng.get('O'),
            'contract_data_sng_usd': contract_data_sng.get('N'),
            'contract_data_sng_rub': contract_data_sng.get('M'),
            'contract_data_sng_byn': contract_data_sng.get('P'),
            'ip_data_sng_eur': ip_data_sng.get('O'),
            'ip_data_sng_usd': ip_data_sng.get('N'),
            'ip_data_sng_rub': ip_data_sng.get('M'),
            'ip_data_sng_byn': ip_data_sng.get('P'),
            'samozanyatii_data_sng_eur': samozanyatii_data_sng.get('O'),
            'samozanyatii_data_sng_usd': samozanyatii_data_sng.get('N'),
            'samozanyatii_data_sng_rub': samozanyatii_data_sng.get('M'),
            'samozanyatii_data_sng_byn': samozanyatii_data_sng.get('P'),
        }
        
        date_for_eur_rate_sheet = {
            'id' : resume_id,
            'contract_data_eur': contract_data_es.get('O'),
            'contract_data_usd': contract_data_es.get('N'),
            'contract_data_rub': contract_data_es.get('M'),
            'contract_data_byn': contract_data_es.get('P'),
            'ip_data_eur': ip_data_es.get('O'),
            'ip_data_usd': ip_data_es.get('N'),
            'ip_data_rub': ip_data_es.get('M'),
            'ip_data_byn': ip_data_es.get('P'),
            'samozanyatii_data_eur': samozanyatii_data_es.get('O'),
            'samozanyatii_data_usd': samozanyatii_data_es.get('N'),
            'samozanyatii_data_rub': samozanyatii_data_es.get('M'),
            'samozanyatii_data_byn': samozanyatii_data_es.get('P'),
        }
        date_for_eu_sng_rates = {
            'Рейт для Заказчика (СНГ)' : data_for_sng_rate_sheet,
            'Рейт для Заказчика (ЕС/США)' : date_for_eur_rate_sheet,
            
        }
        
        for k, v in date_for_eu_sng_rates.items():
            print(f"Добавление {v} в Google таблицу...")
            success = await add_data_to_worksheet(v, worksheet_name=k)
            if success:
                print(f"📊 {k} добавлено в Google таблицу!")
            else:
                await message.answer(f"⚠️ Не удалось добавить {k} в Google таблицу. Проверьте настройки.")
                
                
        rate_sng_for_main_table = f"Штат/контракт-{data_for_sng_rate_sheet.get('contract_data_sng_rub')}\nИП-{data_for_sng_rate_sheet.get('ip_data_sng_rub')}\nСамозанятый-{data_for_sng_rate_sheet.get('samozanyatii_data_sng_rub')}"
        rate_eur_for_main_table = f"Штат/контракт-{date_for_eur_rate_sheet.get('contract_data_usd')}\nИП-{date_for_eur_rate_sheet.get('ip_data_usd')}\nСамозанятый-{date_for_eur_rate_sheet.get('samozanyatii_data_usd')}"
        
        
    except Exception as e:
        await message.answer(f"⚠️ Не удалось добавить данные о ставках в Google таблицу. Проверьте настройки.")       
    else:
        salary = None
        
    
    data_for_resume_sheet = {
        "resume_id": resume_id,
        "last_name": (resume_data.get("lastName") or {}).get("ru") or (resume_data.get("lastName") or {}).get("en") or "не указано",
        "first_name": (resume_data.get("firstName") or {}).get("ru") or (resume_data.get("firstName") or {}).get("en") or "не указано",
        "middle_name": (resume_data.get("patronymic") or {}).get("ru") or (resume_data.get("patronymic") or {}).get("en") or "не указано",
        "specialization": ", ".join([k for k, v in resume_data.get("specialization", {}).items() if v]),
        "date_of_birth": resume_data.get("dateOfBirth") or "не указано",
        "location": ", ".join(filter(None, [
            ", ".join(resume_data.get("city", {}).get("ru")) if isinstance(resume_data.get("city", {}).get("ru"), list)
            else resume_data.get("city", {}).get("ru") if resume_data.get("city") else None,

            ", ".join(resume_data.get("location", {}).get("ru")) if isinstance(resume_data.get("location", {}).get("ru"), list)
            else resume_data.get("location", {}).get("ru") if resume_data.get("location") else None,
        ])) or "не указано",
        "grade": ", ".join([k for k, v in resume_data.get("grade", {}).items() if v]) or "не указано",
        "total_experience": resume_data.get("totalExperience") or "не указано",
        "special_experience": resume_data.get("specialExperience") or "не указано",
        'program_languages': ", ".join([k for k, v in resume_data.get('programmingLanguages', {}).items() if v]) or "не указано",
        'frameworks': ", ".join([k for k, v in resume_data.get('frameworks', {}).items() if v]) or "не указано",
        'technologies': ", ".join([k for k, v in resume_data.get('technologies', {}).items() if v]) or "не указано",
        'project_industries' : ", ".join([k for k, v in resume_data.get('projectIndustries', {}).items() if v]) or "не указано",
        'languague' : ", ".join([f"{k}: {v}" for k, v in resume_data.get('languages', {}).items() if v and v != False]) or "не указано",
        'portfolio' : ", ".join([k for k, v in resume_data.get('portfolio', {}).items() if v]) or "не указано",
        'contacts': '\n'.join(filter(None, [
            resume_data.get('contacts', {}).get('phone'),
            resume_data.get('contacts', {}).get('email'),
            resume_data.get('contacts', {}).get('linkedin'),
            resume_data.get('contacts', {}).get('telegram'),
            resume_data.get('contacts', {}).get('skype'),
            resume_data.get('contacts', {}).get('github'),
            resume_data.get('contacts', {}).get('gitlab'),
            resume_data.get('contacts', {}).get('whatsapp'),
            resume_data.get('contacts', {}).get('viber'),
            resume_data.get('contacts', {}).get('discord'),
            resume_data.get('contacts', {}).get('slack'),
            resume_data.get('contacts', {}).get('microsoftTeams'),
            resume_data.get('contacts', {}).get('zoom'),
            resume_data.get('contacts', {}).get('googleMeet'),
            resume_data.get('contacts', {}).get('facebook'),
            resume_data.get('contacts', {}).get('instagram'),
            resume_data.get('contacts', {}).get('twitter'),
            resume_data.get('contacts', {}).get('vk'),
            resume_data.get('contacts', {}).get('tiktok'),
            resume_data.get('contacts', {}).get('reddit'),
            resume_data.get('contacts', {}).get('stackoverflow'),
            resume_data.get('contacts', {}).get('habrCareer')
        ])) or "не указано",
        
        "salary_expectations": salary_expectations or "не указано",
        "rate_sng": rate_sng_for_main_table or "не указано",
        "rate_eur": rate_eur_for_main_table or "не указано",
        "availability": ", ".join([k for k, v in resume_data.get('availability', {}).items() if v]) if isinstance(resume_data.get('availability'), dict) else resume_data.get('availability', '') or "не указано",
        "date_of_exit": ".",
        'resume_url' : file_url,
        'new_resume_url_russian' : new_resume_url_russian or '-',
        'new_resume_url_english' : new_resume_url_english or '-',
        'rekruiter_username' : '@' + rekruter_username,
        'date_add_for_rekruiter' : datetime.now().strftime("%Y-%m-%d %H:%M:%S") if user_id != ADMIN_ID else '-',
        'date_add_for_admin' : datetime.now().strftime("%Y-%m-%d %H:%M:%S") if user_id == ADMIN_ID else '-',
    }
    
    data_for_name_sheet = build_row(resume_id, resume_data.get("firstName"), NAME_MAP)
    
    data_for_surname_sheet = build_row(resume_id, resume_data.get("lastName"), SURNAME_MAP)
    
    data_for_roles_sheet = build_row_symbols(resume_id, resume_data.get("specialization"), ROLES_MAP)

    data_for_location_sheet = {
        "resume_id": resume_id,
        "location_ru": (resume_data.get("location") or {}).get("ru") or "❌",
        "city_ru": (resume_data.get("city") or {}).get("ru") or "❌",
        "location_en": (resume_data.get("location") or {}).get("en") or "❌",
        "city_en": (resume_data.get("city") or {}).get("en") or "❌",
    }
    
    data_for_grade_sheet = build_row_symbols(resume_id, resume_data.get("grade"), GRADE_MAP)
    
    data_for_programm_lang_sheet = build_row_symbols(resume_id, resume_data.get("programmingLanguages"), PROGRAM_LANG_MAP)
    
    data_for_frameworks_sheet = build_row_symbols(resume_id, resume_data.get("frameworks"), FRAMEWORKS_MAP)
    
    data_for_tech_sheet = build_row_symbols(resume_id, resume_data.get("technologies"), TECH_MAP)
    
    data_for_project_industries_sheet = build_row_symbols(resume_id, resume_data.get("projectIndustries"), PRODUCT_INDUSTRIES_MAP)
    
    data_for_language_sheet = build_row(resume_id, resume_data.get('languages'), LANG_MAP)
    
    data_for_portfolio_sheet = build_row(resume_id, resume_data.get("portfolio"), PORTFOLIO_MAP)
    
    data_for_work_time_sheet = build_row_symbols(resume_id, resume_data.get('workTime'), WORK_TIME_MAP)
    
    data_for_work_form_sheet = build_row_symbols(resume_id, resume_data.get('workForm'), WORK_FORM_MAP)
    
    data_for_contacts_sheet = build_row(resume_id, resume_data.get('contacts'), CONTACTS_MAP)
    
    data_for_avaliable_sheet = build_row_symbols(resume_id, resume_data.get('availability'), AVAILABILITY_MAP)

    
    
    data_for_table = {
        'Свободные ресурсы на аутстафф': data_for_resume_sheet,
        'Фамилия' : data_for_surname_sheet,
        'Имя' : data_for_name_sheet,
        'Должности/Специализации' : data_for_roles_sheet,
        'Локация' : data_for_location_sheet,
        'Грейды специалистов' : data_for_grade_sheet,
        'Языки программирования' : data_for_programm_lang_sheet,
        'Frameworks & Libraries' : data_for_frameworks_sheet,
        'Технологии и инструменты' : data_for_tech_sheet,
        'Отрасли проектов' : data_for_project_industries_sheet,
        'Иностранные языки' : data_for_language_sheet,
        'Портфолио' : data_for_portfolio_sheet,
        'Формат работы' : data_for_work_time_sheet,
        'Форма трудоустройства' : data_for_work_form_sheet,
        'Контакты' : data_for_contacts_sheet,
        'Доступность кандидатов' : data_for_avaliable_sheet,
    }
  
    
    
    for k, v in data_for_table.items():
        print(f"Добавление {v} в Google таблицу...")
        success = await add_data_to_worksheet(v, worksheet_name=k)
        if success:
            print(f"📊 {k} добавлено в Google таблицу!")
        else:
            await message.answer(f"⚠️ Не удалось добавить {k} в Google таблицу. Проверьте настройки.")
    
    
    # Сообщение об успехе будет отправлено в конце цикла
    await message.answer(f"✅ Резюме '{file_name}' успешно добавлено!")


@scan_router.callback_query(F.data == 'delete_record')
async def show_delete_menu(callback: types.CallbackQuery, state: FSMContext):
    """Запрашивает ID для удаления"""
    await callback.message.delete()
    await callback.message.answer("🗑️ Введите ID записи для удаления:")
    await state.set_state(DeleteRecord.waiting_for_id)


@scan_router.message(DeleteRecord.waiting_for_id)
async def process_delete_id(message: types.Message, state: FSMContext):
    """Обрабатывает введенный ID и запрашивает подтверждение"""
    await state.clear()
    resume_id = message.text.strip()

    # Подтверждение удаления
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    confirm_kb = InlineKeyboardBuilder()
    confirm_kb.button(text="✅ Да, удалить", callback_data=f"confirm_delete_{resume_id}")
    confirm_kb.button(text="❌ Отмена", callback_data="cancel_delete")
    confirm_kb.adjust(1)

    await message.answer(
        f"⚠️ Вы уверены, что хотите удалить запись с ID: {resume_id}?\n\n"
        f"Это действие удалит все данные кандидата из всех листов таблицы и не может быть отменено!",
        reply_markup=confirm_kb.as_markup()
    )


@scan_router.callback_query(F.data.startswith('confirm_delete_'))
async def confirm_delete_record(callback: types.CallbackQuery):
    """Подтверждает и выполняет удаление записи"""
    await callback.message.delete()
    
    # Извлекаем ID из callback_data
    resume_id = callback.data.replace('confirm_delete_', '')
    
    await callback.message.answer(f"🗑️ Удаляю запись с ID: {resume_id}...")
    
    # Выполняем удаление
    success = delete_resume_by_id(resume_id)
    
    if success:
        await callback.message.answer(
            f"✅ Запись с ID {resume_id} успешно удалена из всех листов таблицы!",
            reply_markup=await start_kb(),
            
        )
    else:
        await callback.message.answer(
            f"❌ Не удалось удалить запись с ID {resume_id}. Проверьте подключение к Google Sheets.",
            reply_markup=await start_kb(),
            
        )


@scan_router.callback_query(F.data == 'cancel_delete')
async def cancel_delete(callback: types.CallbackQuery):
    """Отменяет удаление и возвращает в главное меню"""
    await callback.message.delete()
    await callback.message.answer("❌ Удаление отменено", reply_markup=await start_kb())


