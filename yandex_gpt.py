from typing import List, Tuple
import urllib.parse
import aiohttp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class YandexGPT:
    def __init__(self, api_key: str, folder_id: str, LANDMARKS):
        self.api_key = api_key
        self.folder_id = folder_id
        self.url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self.LANDMARKS = LANDMARKS
    
    async def generate_text(self, prompt: str, temperature: float = 0.3) -> str:
        #Генерация текста через YandexGPT
        try:
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
                "completionOptions": {
                    "stream": False,
                    "temperature": temperature,
                    "maxTokens": 1000
                },
                "messages": [
                    {
                        "role": "system",
                        "text": """Ты - профессиональный гид по Нижнему Новгороду. 
                        Твоя задача - создавать интересные, информативные и увлекательные описания 
                        достопримечательностей. Будь краток, но информативен. 
                        Используй интересные факты и исторические детали."""
                    },
                    {
                        "role": "user",
                        "text": prompt
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['result']['alternatives'][0]['message']['text']
                    else:
                        error_text = await response.text()
                        print(f"❌ YandexGPT API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ YandexGPT error: {e}")
            return None
    
    async def enhance_landmark_description(self, landmark_name: str, original_data: dict, user_interest: str = "") -> str:
        #Улучшение описания достопримечательности с помощью YandexGPT
        
        prompt = f"""
        Создай краткое и увлекательное описание достопримечательности для туриста.
        
        Название: {landmark_name}
        Категория: {original_data.get('category', 'достопримечательность')}
        Особенности: {', '.join(original_data.get('features', []))}
        Оригинальное описание: {original_data.get('description', 'нет описания')}
        
        {"Интерес пользователя: " + user_interest if user_interest else ""}
        
        Требования:
        - 2-3 предложения
        - Интересные факты или исторические детали
        - Почему стоит посетить
        - Подходящий для туриста стиль
        - Не использовать маркеры списка
        
        Результат:
        """
        
        enhanced_description = await self.generate_text(prompt)
        return enhanced_description or original_data.get('description', 'Интересное место для посещения.')
    
    async def generate_personal_recommendation(self, route: List[str], user_interest: str, available_time: str) -> str:
        #Генерация персонализированной рекомендации для маршрута
        
        landmarks_info = []
        LANDMARKS = self.LANDMARKS
        for landmark in route[:3]:  # Берем первые 3 для контекста
            if landmark in LANDMARKS:
                data = LANDMARKS[landmark]
                landmarks_info.append(f"{landmark} ({data.get('category', 'достопримечательность')})")
        
        prompt = f"""
        Создай краткое персонализированное введение для туристического маршрута.
        
        Интересы пользователя: {user_interest}
        Доступное время: {available_time}
        Основные точки маршрута: {', '.join(landmarks_info)}
        
        Требования:
        - 1-2 предложения приветствия
        - 2-3 предложения о том, что ждет пользователя
        - Подчеркни соответствие интересам пользователя
        - Энтузиазм и дружелюбный тон
        - Закончи мотивационной фразой
        
        Результат:
        """
        
        recommendation = await self.generate_text(prompt, temperature=0.7)
        return recommendation or f"Отличный маршрут для вас! Наслаждайтесь прогулкой по Нижнему Новгороду! 🌆"


class YandexMaps:
    #Функции для Яндекс Карт
    EMOJI = {
        "start": "🌆", "restart": "🔄", "location": "📍", "time": "⏱️", "route": "🧭",
        "success": "✅", "error": "❌", "welcome": "👋", "interest": "🎯", "loading": "⏳",
        "map": "🗺️", "yandex": "🔵", "walk": "🚶", "distance": "📏", "rating": "⭐",
        "info": "📝", "feature": "✨", "time_visit": "🕒", "category": "🏷️", "next": "➡️",
        "full_route": "🧭", "navigation": "🧭", "food": "🍴", "ai": "🤖"
        }
    
    @staticmethod
    def generate_yandex_map_link(coordinates: Tuple[float, float], place_name: str = "") -> str:
        #Генерирует ссылку на Яндекс Карты для одного места
        lat, lon = coordinates
        encoded_name = urllib.parse.quote(place_name)
        return f"https://yandex.ru/maps/?pt={lon},{lat}&z=17&l=map&text={encoded_name}"
    

    @staticmethod
    def generate_route_map_link(route_landmarks: List[str], start_coords: Tuple[float, float],LANDMARKS) -> str:
        #Генерирует ссылку на Яндекс Карты с построением маршрута
        if not route_landmarks:
            return None
        
        points = [f"{start_coords[0]},{start_coords[1]}"]
        
        for landmark in route_landmarks:
            if landmark in LANDMARKS:
                coords = LANDMARKS[landmark]['coordinates']
                points.append(f"{coords[0]},{coords[1]}")
        
        points_str = "~".join(points)
        return f"https://yandex.ru/maps/?rtext={points_str}&rtt=pd"
    

    @staticmethod
    def generate_individual_map_button(landmark: str,LANDMARKS) -> InlineKeyboardMarkup:
        #Создает кнопку для открытия места на карте
        if landmark not in LANDMARKS:
            return None
        
        coordinates = LANDMARKS[landmark]['coordinates']
        map_url = YandexMaps.generate_yandex_map_link(coordinates, landmark)
        
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{YandexMaps.EMOJI['map']} Открыть на карте", url=map_url)]
        ])
    

    @staticmethod
    def generate_full_route_map_button(route_landmarks: List[str], start_coords: Tuple[float, float],LANDMARKS) -> InlineKeyboardMarkup:
        #Создает кнопку для просмотра всего маршрута на карте
        map_url = YandexMaps.generate_route_map_link(route_landmarks, start_coords,LANDMARKS)
        if not map_url:
            return None
        
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{YandexMaps.EMOJI['navigation']} Весь маршрут на карте", url=map_url)]
        ])
