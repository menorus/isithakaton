from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from yandex_gpt import YandexMaps


class Keybord:
    @staticmethod
    def get_available_categories(LANDMARKS):
        categories = set()
        for landmark_data in LANDMARKS.values():
            categories.add(landmark_data['category'].lower())
        
        print(f"📊 Найдены категории: {categories}")
        return categories

    # Создание клавиатуры на основе категорий
    @staticmethod
    def create_interests_keyboard(LANDMARKS):
        available_categories = Keybord.get_available_categories(LANDMARKS)
        
        CATEGORY_MAPPING = {
            "история": "🏛️ История",
            "архитектура": "🏛️ Архитектура", 
            "музей": "🏛️ Музеи",
            "искусство": "🎨 Искусство",
            "культура": "🎨 Культура",
            "стрит-арт": "🎨 Стрит-арт",
            "парк": "🌳 Парки",
            "природа": "🌳 Природа",
            "отдых": "🌳 Отдых",
            "кафе": "🍴 Еда",
            "ресторан": "🍴 Еда", 
            "еда": "🍴 Еда",
            "кухня": "🍴 Еда",
            "кофе": "🍴 Еда",
            "кофейня": "🍴 Еда",
            "шоппинг": "🛍️ Шоппинг",
            "магазин": "🛍️ Магазины",
            "развлечения": "🎭 Развлечения",
            "театр": "🎭 Театры",
            "кино": "🎭 Кино"
        }
        
        interests_set = set()
        for category in available_categories:
            for key, display_name in CATEGORY_MAPPING.items():
                if key in category:
                    interests_set.add(display_name)
        
        # Если категорий мало, добавляем основные
        if len(interests_set) < 3:
            interests_set.update([
                "🏛️ История", 
                "🎨 Искусство", 
                "🌳 Парки", 
                "🍴 Еда", 
                "🛍️ Шоппинг"
            ])
        
        interests_list = sorted(list(interests_set))
        
        interests_list.append("🌟 Любые достопримечательности")
        
        print(f"🎯 Созданы кнопки интересов: {interests_list}")
        return interests_list

    @staticmethod
    def get_interests_keyboard(INTERESTS_LIST):
        builder = ReplyKeyboardBuilder()
        for interest in INTERESTS_LIST:
            builder.add(KeyboardButton(text=interest))
        builder.adjust(2)
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    
    @staticmethod
    def get_time_keyboard():
        builder = ReplyKeyboardBuilder()
        times = ["1 час", "2 часа", "3 часа", "4 часа"]
        for time in times:
            builder.add(KeyboardButton(text=time))
        builder.adjust(2)
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    @staticmethod
    def get_location_keyboard():
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="📍 Отправить геолокацию", request_location=True))
        builder.add(KeyboardButton(text="📝 Ввести адрес вручную"))
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    
    @staticmethod
    def get_action_keyboard():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{YandexMaps.EMOJI['restart']} Новый маршрут", callback_data="restart")]
        ])