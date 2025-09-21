from aiogram.utils.keyboard import InlineKeyboardBuilder


async def start_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Сканировать резюме", callback_data="scan")
    kb.button(text="Удалить запись", callback_data="delete_record")
    kb.button(text="Добавить информацию", callback_data="add_info")
    kb.adjust(1)
    return kb.as_markup()

async def create_id_selection_kb(ids_list): 
    """Создает клавиатуру с ID кандидатов для удаления (3 в строку)"""
    kb = InlineKeyboardBuilder()
    
    for resume_id in ids_list:
        kb.button(text=resume_id, callback_data=f"delete_{resume_id}")
    
    kb.button(text="❌ Отмена", callback_data="cancel_delete")
    kb.adjust(3)  # 3 кнопки в строку
    return kb.as_markup()

async def add_info_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Имя", callback_data="name")
    kb.button(text="Фамилия", callback_data="surname")
    kb.button(text="Отчество", callback_data="patronymic")
    kb.button(text="Дата рождения", callback_data="date_of_birth")
    kb.button(text="Языки", callback_data="languages")
    kb.button(text="Локация", callback_data="location")
    kb.button(text="Возможная дата выхода на новое место работы", callback_data="date_of_exit")
    kb.button(text="Зарплатные ожидания (на руки)", callback_data="salary")
    kb.button(text="Контакты", callback_data="add_contacts")
    kb.adjust(2)
    return kb.as_markup()

LANG_LIST = ["English", "German", "French", "Spanish", "Italian", "Chinese (Mandarin)", "Japanese", "Korean", "Portuguese", "Polish", "Arabic", "Turkish", "Hindi", "Ukrainian", "Czech", "Dutch", "Swedish", "Norwegian", "Finnish"]


async def add_lang_kb():
    kb = InlineKeyboardBuilder()
    for lang in LANG_LIST:
        kb.button(text = lang, callback_data=lang)
    kb.adjust(3)
    return kb.as_markup()
    
async def add_new_lang_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data="add_new_lang")
    kb.button(text="Нет", callback_data="cancel_add_new_lang")
    kb.adjust(1)
    return kb.as_markup()
    
    
    
CONTACTS_LIST = ["Telegram", "GitHub/GitLab", "Телефон", "E-mail", "LinkedIn", "Skype", "WhatsApp", "Viber", "Discord", "Slack", "Microsoft Teams", "Zoom", "Google Meet", "Facebook", "Instagram", "X (Twitter)", "VK", "TikTok", "Reddit", "Stack Overflow", "Habr Career"]


async def add_contacts_kb():
    kb = InlineKeyboardBuilder()
    for contact in CONTACTS_LIST:
        kb.button(text = contact, callback_data=contact)
    kb.adjust(3)
    return kb.as_markup()
    
    
async def add_contacts_confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Да", callback_data="add_new_contacts")
    kb.button(text="Нет", callback_data="cancel_add_contacts")
    kb.adjust(1)
    return kb.as_markup()
    
    
def get_yes_no_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да", callback_data="add_more_yes")
    kb.button(text="❌ Нет", callback_data="add_more_no")
    kb.adjust(2)
    return kb.as_markup()