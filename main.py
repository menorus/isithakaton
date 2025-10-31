import asyncio
from geopy.geocoders import Nominatim
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config
from yandex_gpt import YandexGPT,YandexMaps
from optimazer import RouteOptimizer
from parserxsl import Parser
from keybords import Keybord

LANDMARKS = Parser.output_lendmarks()

bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher()

user_data = {}

# Инициализация YandexGPT 
yandex_gpt = YandexGPT(
    api_key=getattr(config, 'YANDEX_GPT_API_KEY', ''),
    folder_id=getattr(config, 'YANDEX_FOLDER_ID', ''),
    LANDMARKS = LANDMARKS
)

INTERESTS_LIST = Keybord.create_interests_keyboard(LANDMARKS)
route_optimizer = RouteOptimizer(LANDMARKS)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id] = {"step": "waiting_interest"}
    
    welcome_text = f"""
{YandexMaps.EMOJI['welcome']} **Добро пожаловать в ваш персональный AI-гид по Нижнему Новгороду!** 🌆

✨ **Что я умею:**
• 🎯 Создаю маршруты по вашим интересам
• ⏱️ Подбираю оптимальное количество мест под ваше время
• 🤖 Генерирую уникальные описания с помощью AI
• 🗺️ Строю удобные маршруты с навигацией

🚀 **Как это работает:**
1. Выберите что вам интересно {YandexMaps.EMOJI['interest']}
2. Укажите сколько времени есть {YandexMaps.EMOJI['time']}
3. Отправьте ваше местоположение {YandexMaps.EMOJI['location']}
4. Получите готовый маршрут! {YandexMaps.EMOJI['route']}

🎨 **Доступные интересы:**
• Архитектура и история 🏛️
• Искусство и культура 🎨  
• Парки и природа 🌳
• Кафе и рестораны 🍴
• Шоппинг и развлечения 🛍️
• И многое другое!

{YandexMaps.EMOJI['ai']} *Все описания создаются искусственным интеллектом специально для вас*


👇 **Выберите, что вас интересует, и начнем наше путешествие!**
"""
    
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=Keybord.get_interests_keyboard(INTERESTS_LIST))

@dp.message(lambda message: message.text == "📝 Ввести адрес вручную")
async def handle_manual_location_request(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_data or user_data[user_id].get("step") != "waiting_location":
        user_data[user_id] = {"step": "waiting_interest"}
        await message.answer("Давайте начнем сначала. Выберите интерес:", reply_markup=Keybord.get_interests_keyboard(INTERESTS_LIST))
        return
    
    user_data[user_id]["step"] = "waiting_address"
    
    await message.answer(
        f"{YandexMaps.EMOJI['location']} **Напишите ваш адрес:**\n(Например: ул. Большая Покровская, 1)",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )

@dp.message(lambda message: user_data.get(message.from_user.id, {}).get("step") == "waiting_address")
async def handle_address_input(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]["step"] = "processing_address"
    
    loading_msg = await message.answer(f"{YandexMaps.EMOJI['loading']} **Определяю адрес...**", parse_mode="Markdown")
    
    try:
        geolocator = Nominatim(user_agent="ai-tour-bot")
        location = geolocator.geocode(f"{message.text}, Нижний Новгород")
        
        if not location:
            await loading_msg.edit_text(f"{YandexMaps.EMOJI['error']} **Адрес не найден.** Попробуйте другой вариант.")
            user_data[user_id]["step"] = "waiting_location"
            await message.answer("Выберите способ:", reply_markup=Keybord.get_location_keyboard())
            return
        
        user_data[user_id]["location"] = (location.latitude, location.longitude)
        user_data[user_id]["step"] = "processing"
        
        await loading_msg.edit_text(f"{YandexMaps.EMOJI['success']} **Адрес определен!** Создаю маршрут... {YandexMaps.EMOJI['ai']}")
        await generate_and_send_route(message)
        
    except Exception as e:
        await loading_msg.edit_text(f"{YandexMaps.EMOJI['error']} **Ошибка.** Попробуйте еще раз.")
        user_data[user_id]["step"] = "waiting_location"
        await message.answer("Выберите способ:", reply_markup=Keybord.get_location_keyboard())


async def generate_and_send_route(message: types.Message):
    user_id = message.from_user.id
    user_session = user_data.get(user_id, {})
    
    try:
        interest = user_session.get("interest", "")
        location = user_session.get("location", (56.326887, 44.005986))
        available_time = user_session.get("time", "2 часа")
        
        # Рассчитываем количество мест на основе времени
        places_count = route_optimizer.calculate_places_by_time(available_time)
        
        # Получаем достопримечательности по интересу
        landmarks = route_optimizer.get_landmarks_by_interest(interest, max_landmarks=15)
        
        if not landmarks:
            await message.answer(
                f"❌ **К сожалению, не нашлось мест по вашему интересу**\n\n"
                f"Попробуйте выбрать другую категорию или 'Любые достопримечательности' 🌟",
                reply_markup=Keybord.get_action_keyboard()
            )
            return
        
        # Создаем маршрут с ограничением по количеству мест
        route = route_optimizer.find_optimal_route(landmarks, location, max_places=places_count)
        
        if not route:
            await message.answer(
                f"❌ **Не удалось построить маршрут**\n\n"
                f"Попробуйте изменить местоположение или выбрать другие интересы 🔄",
                reply_markup=Keybord.get_action_keyboard()
            )
            return
        
        # Сохраняем маршрут в сессии
        user_data[user_id]["current_route"] = route
        
        # Обновляем рейтинги для мест в маршруте
        rating_update_msg = await message.answer(
            f"🔍 **Обновляю актуальные рейтинги...**\n"
            f"⏳ *Запрашиваю свежие оценки из Яндекс Карт*"
        )
        
        for landmark in route:
            if landmark in LANDMARKS:
                try:
                    if yandex_data and yandex_data.get('rating'):
                        LANDMARKS[landmark]['yandex_rating'] = yandex_data['rating']
                        LANDMARKS[landmark]['yandex_data'] = yandex_data
                    await asyncio.sleep(0.3)
                except Exception as e:
                    continue
        
        await rating_update_msg.delete()
        
        ai_intro_message = await message.answer(
            f"🎨 Создаю уникальные описания...\n"
            f"🤖 Искусственный интеллект готовит специально для вас"
        )
        
        personal_recommendation = await yandex_gpt.generate_personal_recommendation(
            route, interest, available_time
        )
        
        await ai_intro_message.edit_text("✨ Описания готовы!")
        
        route_map_keyboard = YandexMaps.generate_full_route_map_button(route, location,LANDMARKS)
        
        await message.answer(
            f"🎯 **ВАШ ПЕРСОНАЛЬНЫЙ МАРШРУТ ГОТОВ!**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 **ОСНОВНАЯ ИНФОРМАЦИЯ**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎯 **Интерес:** {interest}\n"
            f"⏱️ **Время:** {available_time}\n"
            f"📍 **Количество мест:** {len(route)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💫 **ПЕРСОНАЛЬНАЯ РЕКОМЕНДАЦИЯ**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"_{personal_recommendation}_\n\n"
            f"👇 **Нажмите кнопку ниже для просмотра маршрута на карте**",
            parse_mode="Markdown",
            reply_markup=route_map_keyboard
        )
        
        # Отправляем каждое место отдельным сообщением
        for i, landmark in enumerate(route, 1):
            if landmark in LANDMARKS:
                landmark_data = LANDMARKS[landmark]
                
                # Генерируем улучшенное описание
                enhanced_description = await yandex_gpt.enhance_landmark_description(
                    landmark, landmark_data, interest
                )
                
                # Используем рейтинг из Яндекс Карт если есть
               # current_rating = landmark_data.get('yandex_rating') or landmark_data['rating']
               # rating_source = "⭐ Яндекс Карты" if landmark_data.get('yandex_rating') else "⭐ База данных"
                
                landmark_message = (
                    f"📍 **{i}. {landmark}**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📖 **Описание:**\n"
                    f"_{enhanced_description}_\n\n"
                )
                
                # Добавляем информацию из Яндекс Карт если есть
                yandex_data = landmark_data.get('yandex_data', {})
                if yandex_data.get('address'):
                    landmark_message += f"🏠 **Адрес:** {yandex_data['address']}\n"
                
                if yandex_data.get('reviews'):
                    landmark_message += f"💬 **Отзывов:** {yandex_data['reviews']}\n"
                
                if landmark_data.get('features'):
                    features = " | ".join([f"✨ {f}" for f in landmark_data['features'][:3]])
                
                
                # Получаем кнопку для карты
                map_keyboard = YandexMaps.generate_individual_map_button(landmark,LANDMARKS)
                
                await message.answer(landmark_message, parse_mode="Markdown", reply_markup=map_keyboard)
                await asyncio.sleep(0.5)
        
        # Считаем средний рейтинг маршрута
        total_rating = 0
        rated_places = 0
        for landmark in route:
            if landmark in LANDMARKS:
                rating = LANDMARKS[landmark].get('yandex_rating') or LANDMARKS[landmark]['rating']
                total_rating += rating
                rated_places += 1
        
        avg_rating = total_rating / rated_places if rated_places > 0 else 0
        
        # Финальное сообщение с кнопками
        final_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🗺️ Посмотреть весь маршрут на карте", 
                                url=YandexMaps.generate_route_map_link(route, location,LANDMARKS))],
            [InlineKeyboardButton(text=f"🔄 Создать новый маршрут", callback_data="restart")]
        ])
        
        await message.answer(
            f"🎉 МАРШРУТ УСПЕШНО СОЗДАН!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 ИТОГИ\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Готово: Персональный маршрут\n"
            f"⏱️ Время прогулки: {available_time}\n"
            f"📍 Точек посещения: {len(route)}\n"
            f"🎯 Категория: {interest}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 СОВЕТЫ ДЛЯ ПУТЕШЕСТВЕННИКА\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🗺️ Используйте Яндекс Карты для навигации\n"
            f"📸 Не забывайте фотографировать красивые места\n"
            f"⏰ Учитывайте время на дорогу между точками\n"
            f"🎒 Берите удобную обувь для прогулки\n\n"
            f"✨ Приятного путешествия по Нижнему Новгороду! 🌆",
            reply_markup=final_keyboard
        )
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await message.answer(
            f"😔 **К сожалению, произошла ошибка**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 **ПОПРОБУЙТЕ ЕЩЕ РАЗ**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"• Проверьте подключение к интернету\n"
            f"• Попробуйте другой интерес\n"
            f"• Убедитесь в корректности локации\n\n"
            f"👇 Нажмите кнопку ниже для нового маршрута",
            reply_markup=Keybord.get_action_keyboard()
        )

@dp.message(lambda message: message.text in INTERESTS_LIST)
async def handle_interest_selection(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_data or user_data[user_id].get("step") != "waiting_interest":
        user_data[user_id] = {"step": "waiting_interest"}
        await message.answer(
            f"🔄 **Начнем сначала!**\n\n"
            f"👇 Выберите интерес из меню ниже:",
            reply_markup=Keybord.get_interests_keyboard(INTERESTS_LIST)
        )
        return
    
    user_data[user_id] = {
        "step": "waiting_time",
        "interest": message.text
    }
    
    response_text = (
        f"✅ **Отличный выбор!** {message.text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏰ **ВЫБЕРИТЕ ВРЕМЯ ПРОГУЛКИ**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ **Рекомендации по времени:**\n\n"
        f"• 🕐 1 час → 2 места\n"
        f"• 🕑 2 часа → 3 места  \n"
        f"• 🕒 3 часа → 4 места\n"
        f"• 🕓 4 часа → 5 мест\n\n"
        f"👇 **Выберите подходящий вариант:**"
    )
    
    await message.answer(response_text, parse_mode="Markdown", reply_markup=Keybord.get_time_keyboard())

@dp.message(lambda message: message.text in ["1 час", "2 часа", "3 часа", "4 часа"])
async def handle_time_selection(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_data or user_data[user_id].get("step") != "waiting_time":
        user_data[user_id] = {"step": "waiting_interest"}
        await message.answer(
            f"🔄 **Начнем сначала!**\n\n"
            f"👇 Выберите интерес из меню ниже:",
            reply_markup=Keybord.get_interests_keyboard(INTERESTS_LIST)
        )
        return
    
    user_data[user_id]["step"] = "waiting_location"
    user_data[user_id]["time"] = message.text
    
    # Рассчитываем количество мест
    places_count = route_optimizer.calculate_places_by_time(message.text)
    
    response_text = (
        f"✅ **Запомнил!** {message.text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📍 **УКАЖИТЕ ВАШЕ МЕСТОПОЛОЖЕНИЕ**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 **Будет подобрано:** {places_count} мест\n\n"
        f"✨ **Доступные способы:**\n\n"
        f"• 📍 Отправить геолокацию (рекомендуется)\n"
        f"• 📝 Ввести адрес вручную\n\n"
        f"👇 **Выберите удобный способ:**"
    )
    
    await message.answer(response_text, parse_mode="Markdown", reply_markup=Keybord.get_location_keyboard())

@dp.message(lambda message: message.location is not None)
async def handle_location(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_data or user_data[user_id].get("step") != "waiting_location":
        user_data[user_id] = {"step": "waiting_interest"}
        await message.answer(
            f"🔄 **Начнем сначала!**\n\n"
            f"👇 Выберите интерес из меню ниже:",
            reply_markup=Keybord.get_interests_keyboard(INTERESTS_LIST)
        )
        return
    
    location = message.location
    user_data[user_id]["location"] = (location.latitude, location.longitude)
    user_data[user_id]["step"] = "processing"
    
    await message.answer(
        f"🎨 **СОЗДАЮ ВАШ ПЕРСОНАЛЬНЫЙ МАРШРУТ...**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔄 **ЭТАПЫ ОБРАБОТКИ**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 Поиск лучших мест...\n"
        f"🗺️ Построение маршрута...\n"
        f"⭐ Обновление рейтингов...\n"
        f"🤖 Генерация описаний...\n\n"
        f"⏳ *Это займет несколько секунд*",
        parse_mode="Markdown"
    )
    await generate_and_send_route(message)

@dp.callback_query(lambda c: c.data == "restart")
async def handle_restart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_data[user_id] = {"step": "waiting_interest"}
    
    await callback.answer("✨ Начинаем новый маршрут!")
    await callback.message.answer(
        f"🔄 **СОЗДАЕМ НОВЫЙ МАРШРУТ**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **ВЫБЕРИТЕ ИНТЕРЕС**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✨ Куда отправимся на этот раз?\n\n"
        f"👇 **Выберите категорию из меню:**",
        parse_mode="Markdown",
        reply_markup=Keybord.get_interests_keyboard(INTERESTS_LIST)
    )

@dp.message()
async def handle_other_messages(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        await message.answer(f"{YandexMaps.EMOJI['welcome']} Напишите /start чтобы начать!")
        return
    
    current_step = user_data[user_id].get("step", "")
    
    if current_step == "waiting_interest":
        await message.answer("Пожалуйста, выберите интерес из меню ниже:", reply_markup=Keybord.get_interests_keyboard(INTERESTS_LIST))
    elif current_step == "waiting_time":
        await message.answer("Пожалуйста, выберите время из меню ниже:", reply_markup=Keybord.get_time_keyboard())
    elif current_step == "waiting_location":
        await message.answer("Пожалуйста, выберите способ указания локации:", reply_markup=Keybord.get_location_keyboard())
    elif current_step == "waiting_address":
        await message.answer("Пожалуйста, введите ваш адрес в Нижнем Новгороде:")
    else:
        await message.answer(f"{YandexMaps.EMOJI['error']} Не понимаю команду. Напишите /start чтобы начать заново.")

async def main():
    print(f"🚀 Бот запущен! Готов к работе...")
    print(f"📍 Загружено достопримечательностей: {len(LANDMARKS)}")
    
    # Проверяем доступность YandexGPT
    if hasattr(config, 'YANDEX_GPT_API_KEY') and config.YANDEX_GPT_API_KEY:
        print(f"🤖 YandexGPT: ВКЛЮЧЕН")
    else:
        print(f"⚠️ YandexGPT: ОТКЛЮЧЕН (добавьте ключи в config.py)")
    
    # Выводим статистику по категориям
    categories_count = {}
    for name, data in LANDMARKS.items():
        category = data['category']
        categories_count[category] = categories_count.get(category, 0) + 1
    
    print("📊 Статистика по категориям:")
    for category, count in categories_count.items():
        print(f"  - {category}: {count} объектов")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())