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
from google_sheet import *

load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN'))
add_info_router = Router()

lang_dict = {}
contacts_dict = {}

class SelectResume(StatesGroup):
    resume_id = State()
    waiting_for_category = State()  


class AddName(StatesGroup):
    name = State()
    eng_name = State()

class AddSurname(StatesGroup):
    surname = State()
    eng_surname = State()

class AddPatronymic(StatesGroup):
    patronymic = State()
    

class AddDateOfBirth(StatesGroup):
    date_of_birth = State()

class AddLanguages(StatesGroup):
    languages = State()
    level = State()
    wait_for_new_lang = State()

class AddLocation(StatesGroup):
    country = State()
    city = State()

class AddDateOfExit(StatesGroup):
    date_of_exit = State()

class AddSalary(StatesGroup):
    salary = State()
    wait_for_new_salary = State()

class AddContacts(StatesGroup):
    contacts = State()
    wait_for_new_contact = State()


@add_info_router.callback_query(F.data == "add_info")
async def add_info(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите айди резюме")
    await state.set_state(SelectResume.resume_id)
    
    
@add_info_router.message(SelectResume.resume_id)
async def select_resume(message: types.Message, state: FSMContext):
    resume_id = message.text.strip()
    await message.answer(f"Выберете категорию", reply_markup=await add_info_kb())
    await state.set_state(SelectResume.waiting_for_category)
    await state.update_data(resume_id=resume_id)
    
    
@add_info_router.callback_query(F.data == "name", SelectResume.waiting_for_category)
async def name(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    await callback.message.answer("Введите имя")
    await state.set_state(AddName.name)
    await state.update_data(resume_id=data['resume_id'])
    
@add_info_router.message(AddName.name)
async def name_eng(message: types.Message, state: FSMContext):
    await message.answer("Введите английское имя")
    await state.set_state(AddName.eng_name)
    await state.update_data(name=message.text.strip())
    
@add_info_router.message(AddName.eng_name)
async def name_add(message: types.Message, state: FSMContext):
    data = await state.get_data()
    eng_name = message.text.strip()
    resume_id = data['resume_id']
    name = data['name']
    
    update_data = {
        'На русском' : name,
        'На английском' : eng_name
    }
    
    sucsess = update_resume_by_id(resume_id=resume_id, update_data=update_data, worksheet_name='Имя')
    two_sucsess = update_cell_by_id_and_column(resume_id, 'Имя', name)
    
    if sucsess and two_sucsess:
        await message.answer('✅Данные обновлены')
    else:
        await message.answer('❌ Не удалось обновить данные')


@add_info_router.callback_query(F.data == "surname", SelectResume.waiting_for_category)
async def surname(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    await callback.message.delete()
    await callback.message.answer("Введите фамилию")
    await state.set_state(AddSurname.surname)
    await state.update_data(resume_id=resume_id)
    
    
@add_info_router.message(AddSurname.surname)
async def surname_eng(message: types.Message, state: FSMContext):
    await message.answer("Введите английскую фамилию")
    await state.set_state(AddSurname.eng_surname)
    await state.update_data(surname=message.text.strip())
    
@add_info_router.message(AddSurname.eng_surname)
async def surname_add(message: types.Message, state: FSMContext):
    data = await state.get_data()
    eng_name = message.text.strip()
    resume_id = data['resume_id']
    name = data['surname']
    
    update_data = {
        'На русском' : name,
        'На английском' : eng_name
    }
    
    sucsess = update_resume_by_id(resume_id=resume_id, update_data=update_data, worksheet_name='Фамилия')
    two_sucsess = update_cell_by_id_and_column(resume_id, 'Фамилия', name)
    
    if sucsess and two_sucsess:
        await message.answer('✅Данные обновлены')
        
    await state.clear()
    
@add_info_router.callback_query(F.data == "patronymic", SelectResume.waiting_for_category)
async def patronymic(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    await callback.message.delete()
    await callback.message.answer("Введите отчество")
    await state.set_state(AddPatronymic.patronymic)
    await state.update_data(resume_id=resume_id)
    

    
@add_info_router.message(AddPatronymic.patronymic)
async def surname_add(message: types.Message, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    patronymic = message.text.strip()
    
    two_sucsess = update_cell_by_id_and_column(resume_id, 'Отчество', patronymic)
    
    if two_sucsess:
        await message.answer('✅Данные обновлены')
    await state.clear()    

        
@add_info_router.callback_query(F.data == "date_of_birth", SelectResume.waiting_for_category)
async def date_of_birth(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    await callback.message.delete()
    await callback.message.answer("Введите дату рождения(формат : 11.11.1111)")
    await state.set_state(AddDateOfBirth.date_of_birth)
    await state.update_data(resume_id=resume_id)
    

    
@add_info_router.message(AddDateOfBirth.date_of_birth)
async def surname_add(message: types.Message, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    date_of_birth = message.text.strip()
    
    
    sucsess = update_cell_by_id_and_column(resume_id, 'Дата рождения', date_of_birth)
    
    if sucsess:
        await message.answer('✅Данные обновлены')
    await state.clear()
    
    
@add_info_router.callback_query(F.data == "languages")
async def languages(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    await callback.message.delete()
    await callback.message.answer("Выберите язык", reply_markup=await add_lang_kb())
    await state.set_state(AddLanguages.languages)
    await state.update_data(resume_id=resume_id)

@add_info_router.callback_query(F.data.in_(LANG_LIST), AddLanguages.languages)
async def languages_lvl(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data
    await callback.message.answer("Введите уровень")
    await state.set_state(AddLanguages.level)
    await state.update_data(languages=lang)


@add_info_router.message(AddLanguages.level)
async def select_new_l(message : types.Message, state : FSMContext):
    lvl = message.text.strip()
    data = await state.get_data()
    lang = data.get('languages')
    await message.answer('Добавить еще язык?', reply_markup=await add_new_lang_kb())
    lang_dict.update({lang : lvl})
    
    
@add_info_router.callback_query(F.data == "add_new_lang", AddLanguages.level)
async def add_new_lang(callback: types.CallbackQuery, state: FSMContext):
    await languages(callback, state)

@add_info_router.callback_query(F.data == "cancel_add_new_lang", AddLanguages.level)
async def cancel_add_new_lang(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    
    lang_str = ", ".join([f"{lang}: {lvl}" for lang, lvl in lang_dict.items()])
    
    sucsess = update_resume_by_id(resume_id=resume_id, update_data=lang_dict, worksheet_name='Иностранные языки')
    two_sucsess = update_cell_by_id_and_column(resume_id, 'Иностранные языки', lang_str)
    
    if sucsess and two_sucsess:
        await callback.message.answer('✅Данные обновлены')
    else:
        await callback.message.answer('❌ Не удалось обновить данные')
    await state.clear()
    lang_dict.clear()

@add_info_router.callback_query(F.data == "date_of_exit", SelectResume.waiting_for_category)
async def date_of_exit(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    await callback.message.delete()
    await callback.message.answer("Введите дату выхода на новое место работы(формат : 11.11.1111)")
    await state.set_state(AddDateOfExit.date_of_exit)
    await state.update_data(resume_id=resume_id)

@add_info_router.message(AddDateOfExit.date_of_exit)
async def date_of_exit_add(message: types.Message, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    date_of_exit = message.text.strip()
    
    two_sucsess = update_cell_by_id_and_column(resume_id, 'Возможная дата выхода на новое место работы', date_of_exit)
    
    if two_sucsess:
        await message.answer('✅Данные обновлены')
    await state.clear()


@add_info_router.callback_query(F.data == "location")
async def location(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    await callback.message.delete()
    await callback.message.answer("Введите страну")
    await state.set_state(AddLocation.country)
    await state.update_data(resume_id=resume_id)
    
@add_info_router.message(AddLocation.country)
async def location_add(message: types.Message, state: FSMContext):
    
    country = message.text.strip()
    await message.answer("Введите город")
    await state.set_state(AddLocation.city)
    await state.update_data(country=country)

@add_info_router.message(AddLocation.city)
async def location_add(message: types.Message, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    city = message.text.strip()
    
    update_data = {
        'Страна' : data['country'],
        'Город' : city
    }
    
    location = data['country'] + ', ' + city
    
    sucsess = update_resume_by_id(resume_id=resume_id, update_data=update_data, worksheet_name='Локация')
    two_sucsess = update_cell_by_id_and_column(resume_id, 'Локация', location)
    
    if sucsess and two_sucsess:
        await message.answer('✅Данные обновлены')
    await state.clear()

@add_info_router.callback_query(F.data == "salary")
async def salary(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    await callback.message.delete()
    await callback.message.answer("Введите зарплатные ожидания строго в формате 100000 USD")
    await state.set_state(AddSalary.salary)
    await state.update_data(resume_id=resume_id)
    
@add_info_router.message(AddSalary.salary)
async def salary_add(message: types.Message, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    salary = message.text.strip()
    value = salary.split(" ")[0]
    if not value.isdigit():
        await message.answer('❌ Вы ввели не число')
        return
    value = int(value)
    sucsess = update_cell_by_id_and_column(resume_id, 'Зарплатные ожидания (на руки)', salary)
    
    
    currency = salary.split(" ")[1].upper()
    print(currency)
    
    if currency == "RUB":
        search_col = "B"
    elif currency == "BYN":
        search_col = "E"
    elif currency == "USD":
        search_col = "C"
    elif currency == "EUR":
        search_col = "D"
    else:
        await message.answer('Неверная валюта')
        return
    
    contract_data_sng = search_and_extract_values(search_col, value, ["M",'N','O','P'], "Рассчет ставки (штат/контракт) СНГ")
    ip_data_sng = search_and_extract_values(search_col, value, ["M",'N','O','P'], "Рассчет ставки (ИП) СНГ")
    samozanyatii_data_sng = search_and_extract_values(search_col, value, ["M",'N','O','P'], "Рассчет ставки (Самозанятый) СНГ")
            
    contract_data_es = search_and_extract_values(search_col, value, ['M','N','O', 'P'], "Рассчет ставки (штат/контракт) ЕС/США")
    ip_data_es = search_and_extract_values(search_col, value, ["M",'N','O','P'], "Рассчет ставки (ИП) ЕС/США")
    samozanyatii_data_es = search_and_extract_values(search_col, value, ["M",'N','O','P'], "Рассчет ставки (Самозанятый) ЕС/США")
    print(contract_data_es)
    print(ip_data_es)
    print(samozanyatii_data_es)
    print(contract_data_sng)
    print(ip_data_sng)
    print(samozanyatii_data_sng)
    try:
        data_for_sng_rate_sheet = {

            'Ставка (штат/контракт) EUR / час': contract_data_sng.get('O'),
            'Ставка (штат/контракт) USD  / час': contract_data_sng.get('N'),
            'Ставка (штат/контракт) RUB / час': contract_data_sng.get('M'),
            'Ставка (штат/контракт) BYN / час': contract_data_sng.get('P'),
            'Ставка (ИП) EUR / час': ip_data_sng.get('O'),
            'Ставка (ИП) USD / час': ip_data_sng.get('N'),
            'Ставка (ИП) RUB / час': ip_data_sng.get('M'),
            'Ставка (ИП) BYN / час': ip_data_sng.get('P'),
            'Ставка (Самозанятый) EUR / час': samozanyatii_data_sng.get('O'),
            'Ставка (Самозанятый) USD  / час': samozanyatii_data_sng.get('N'),
            'Ставка (Самозанятый) RUB / час': samozanyatii_data_sng.get('M'),
            'Ставка (Самозанятый) BYN / час': samozanyatii_data_sng.get('P'),
        }
        
        date_for_eur_rate_sheet = {
            
            'Ставка (штат/контракт) EUR / час': contract_data_es.get('O'),
            'Ставка (штат/контракт) USD  / час': contract_data_es.get('N'),
            'Ставка (штат/контракт) RUB / час': contract_data_es.get('M'),
            'Ставка (штат/контракт) BYN / час': contract_data_es.get('P'),
            'Ставка (ИП) EUR / час': ip_data_es.get('O'),
            'Ставка (ИП) USD  / час': ip_data_es.get('N'),
            'Ставка (ИП) RUB / час': ip_data_es.get('M'),
            'Ставка (ИП) BYN / час': ip_data_es.get('P'),
            'Ставка (Самозанятый) EUR / час': samozanyatii_data_es.get('O'),
            'Ставка (Самозанятый) USD  / час': samozanyatii_data_es.get('N'),
            'Ставка (Самозанятый) RUB / час': samozanyatii_data_es.get('M'),
            'Ставка (Самозанятый) BYN / час': samozanyatii_data_es.get('P'),
        }
        
        
        sucsess = update_resume_by_id(resume_id, data_for_sng_rate_sheet, 'Рейт для Заказчика (СНГ)')
        two_sucsess = update_resume_by_id(resume_id, date_for_eur_rate_sheet, 'Рейт для Заказчика (ЕС/США)')
        if sucsess and two_sucsess:
            await message.answer('✅Данные обновлены')
        else:
            await message.answer('❌ Не удалось обновить данные')
                
    except Exception as e:
        await message.answer(f"⚠️ Не удалось добавить {k} в Google таблицу. Проверьте настройки.")
    
    if sucsess:
        await message.answer('✅Данные обновлены')
    await state.clear()


@add_info_router.callback_query(F.data == "add_contacts")
async def add_contacts(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    resume_id = data['resume_id']
    await callback.message.delete()
    await callback.message.answer("Выберите контакт", reply_markup=await add_contacts_kb())
    await state.set_state(AddContacts.contacts)
    await state.update_data(resume_id=resume_id)

@add_info_router.callback_query(F.data.in_ (CONTACTS_LIST), AddContacts.contacts)
async def contacts_add(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer("Введите контакт(например: @username или ссылка на профиль)")
    await state.set_state(AddContacts.wait_for_new_contact)
    await state.update_data(contact_name=callback.data)
    
@add_info_router.message(AddContacts.wait_for_new_contact)
async def contacts_add_confirm(message: types.Message, state: FSMContext):
    await message.answer("Добавить еще контакт?", reply_markup=await add_contacts_confirm_kb())
    
    contact = message.text.strip()
    data = await state.get_data()
    contact_name = data['contact_name']
    
    contacts_dict.update({contact_name : contact})
    
@add_info_router.callback_query(F.data == "add_new_contacts", AddContacts.wait_for_new_contact)
async def add_new_contacts(callback: types.CallbackQuery, state: FSMContext):
    await add_contacts(callback, state)
    
@add_info_router.callback_query(F.data == "cancel_add_contacts", AddContacts.wait_for_new_contact)
async def cancel_add_contacts(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    data = await state.get_data()
    resume_id = data['resume_id']
    
    contacts_str = ", ".join(contacts_dict.values())
    
    sucsess = update_resume_by_id(resume_id=resume_id, update_data=contacts_dict, worksheet_name='Контакты')
    two_sucsess = update_cell_by_id_and_column(resume_id, 'Контакты', contacts_str)
    
    if sucsess and two_sucsess:
        await callback.message.answer('✅Данные обновлены')
    else:
        await callback.message.answer('❌ Не удалось обновить данные')
    await state.clear()
    contacts_dict.clear()
    
    
    

    
