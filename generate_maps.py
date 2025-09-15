#!/usr/bin/env python3
"""
Скрипт для генерации и добавления переменных-маппингов в maps_for_sheet.py
"""

from google_sheet import generate_and_save_mapping_variables
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    """Генерирует все переменные-маппинги и добавляет их в maps_for_sheet.py"""
    print("🚀 Генерация переменных-маппингов для maps_for_sheet.py...")
    
    # Получаем URL из переменной окружения
    sheet_url = os.getenv('GOOGLE_SHEET_URL')
    
    if not sheet_url:
        print("❌ GOOGLE_SHEET_URL не найден в переменных окружения")
        return
    
    print(f"📊 Используется таблица: {sheet_url}")
    
    # Генерируем и сохраняем переменные в файл
    success = generate_and_save_mapping_variables(sheet_url=sheet_url)
    
    if success:
        print("✅ Все переменные-маппинги успешно добавлены в maps_for_sheet.py")
        print("📝 Теперь у вас есть отдельные переменные для каждого листа:")
        print("   - ФАМИЛИЯ_MAP")
        print("   - ИМЯ_MAP") 
        print("   - ДОЛЖНОСТИ_СПЕЦИАЛИЗАЦИИ_MAP")
        print("   - ЛОКАЦИЯ_MAP")
        print("   - ГРЕЙДЫ_СПЕЦИАЛИСТОВ_MAP")
        print("   - ЯЗЫКИ_ПРОГРАММИРОВАНИЯ_MAP")
        print("   - FRAMEWORKS_&_LIBRARIES_MAP")
        print("   - ТЕХНОЛОГИИ_И_ИНСТРУМЕНТЫ_MAP")
        print("   - ОТРАСЛИ_ПРОЕКТОВ_MAP")
        print("   - ИНОСТРАННЫЕ_ЯЗЫКИ_MAP")
        print("   - ПОРТФОЛИО_MAP")
        print("   - ФОРМАТ_РАБОТЫ_MAP")
        print("   - ФОРМА_ТРУДОУСТРОЙСТВА_MAP")
        print("   - КОНТАКТЫ_MAP")
        print("   - ЗАРПЛАТНЫЕ_ОЖИДАНИЯ_MAP")
        print("   - ДОСТУПНОСТЬ_КАНДИДАТОВ_MAP")
        print("   - РЕЙТ_ДЛЯ_ЗАКАЗЧИКА_(СНГ)_MAP")
        print("   - РЕЙТ_ДЛЯ_ЗАКАЗЧИКА_(ЕС_США)_MAP")
        print("   - РЕКРУТЕР_ПОДРЯДЧИК_MAP")
        print("   - РАССЧЕТ_СТАВКИ_(ШТАТ_КОНТРАКТ)_СНГ_MAP")
        print("   - РАССЧЕТ_СТАВКИ_(ШТАТ_КОНТРАКТ)_ЕС_США_MAP")
        print("   - РАССЧЕТ_СТАВКИ_(ИП)_СНГ_MAP")
        print("   - РАССЧЕТ_СТАВКИ_(ИП)_ЕС_США_MAP")
        print("   - РАССЧЕТ_СТАВКИ_(САМОЗАНЯТЫЙ)_СНГ_MAP")
        print("   - РАССЧЕТ_СТАВКИ_(САМОЗАНЯТЫЙ)_ЕС_США_MAP")
        print("\n💡 Каждая переменная содержит маппинг: {\"ключ в lowercase\": \"Оригинальный Заголовок\"}")
    else:
        print("❌ Ошибка при генерации переменных-маппингов")

if __name__ == "__main__":
    main()
