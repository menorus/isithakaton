from typing import List, Tuple, Dict
from geopy.distance import geodesic
# Обратный маппинг для поиска по категориям 
DISPLAY_TO_CATEGORY_MAPPING = {
    "🏛️ История": ["история", "музей", "памятник", "кремль"],
    "🏛️ Архитектура": ["архитектура", "здание", "собор", "церковь"],
    "🏛️ Музеи": ["музей", "галерея", "выставка"],
    "🎨 Искусство": ["арт", "искусство", "культура", "творчество"],
    "🎨 Культура": ["культура", "театр", "концерт"],
    "🎨 Стрит-арт": ["арт","стрит-арт", "граффити", "уличное искусство"],
    "🌳 Парки": ["парк", "сад", "сквер"],
    "🌳 Природа": ["природа", "ландшафт", "вид"],
    "🌳 Отдых": ["отдых", "прогулка", "развлечение"],
    "🍴 Еда": ["кафе", "ресторан", "еда", "кухня", "кофе", "кофейня", "бар", "бистро", "столовая", "закусочная"],
    "🛍️ Шоппинг": ["шоппинг", "магазин", "торговый"],
    "🛍️ Магазины": ["магазин", "торговый", "шоппинг"],
    "🎭 Развлечения": ["развлечения", "кино", "клуб"],
    "🎭 Театры": ["театр", "спектакль", "сцена"],
    "🎭 Кино": ["кино", "фильм", "кинозал"],
    "🌟 Любые достопримечательности": []  
}

class RouteOptimizer:
    
    def __init__(self, landmarks: Dict):
        self.landmarks = landmarks
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        return geodesic(coord1, coord2).km
    
    
    def get_landmarks_by_interest(self, interest_display: str, max_landmarks: int = 10) -> List[str]:
        relevant_landmarks = []
        
        if interest_display == "🌟 Любые достопримечательности":
            return list(self.landmarks.keys())[:max_landmarks]
        
        search_keywords = DISPLAY_TO_CATEGORY_MAPPING.get(interest_display, [])
        
        if not search_keywords:
            return list(self.landmarks.keys())[:max_landmarks]
        
        print(f"🔍 Поиск по ключевым словам для '{interest_display}': {search_keywords}")
        
        for name, data in self.landmarks.items():
            category_lower = data['category'].lower()
            description_lower = data.get('description', '').lower()
            features_lower = [f.lower() for f in data.get('features', [])]
            
            matches_category = any(keyword in category_lower for keyword in search_keywords)
            matches_description = any(keyword in description_lower for keyword in search_keywords)
            matches_features = any(any(keyword in feature for keyword in search_keywords) for feature in features_lower)
            
            if matches_category or matches_description or matches_features:
                relevant_landmarks.append(name)
        
        if len(relevant_landmarks) < 2:
            all_landmarks = list(self.landmarks.keys())
            # Добавляем случайные, исключая уже выбранные
            additional = [lm for lm in all_landmarks if lm not in relevant_landmarks]
            relevant_landmarks.extend(additional[:max_landmarks - len(relevant_landmarks)])
        
        print(f"🎯 Найдено {len(relevant_landmarks)} мест для интереса '{interest_display}'")
        return relevant_landmarks[:max_landmarks]
    
    def calculate_places_by_time(self, available_time: str) -> int:
        time_mapping = {
            "1 час": 2,   
            "2 часа": 3,  
            "3 часа": 4,  
            "4 часа": 5   
        }
        return time_mapping.get(available_time, 3)
    
    def find_optimal_route(self, landmarks: List[str], start_point: Tuple[float, float], max_places: int = 5) -> List[str]:
        if not landmarks:
            return []
        
        # Сортируем достопримечательности по рейтингу
        landmarks_with_rating = []
        for landmark in landmarks:
            if landmark in self.landmarks:
                rating = self.landmarks[landmark]['rating']
                landmarks_with_rating.append((landmark, rating))
        
        landmarks_with_rating.sort(key=lambda x: x[1], reverse=True)
        
        top_landmarks = [lm[0] for lm in landmarks_with_rating[:max_places]]
        
        if not top_landmarks:
            return []
        
        # Оптимизируем маршрут между выбранными местами
        unvisited = top_landmarks.copy()
        route = []
        current_point = start_point
        
        while unvisited:
            nearest = None
            min_distance = float('inf')
            
            for landmark in unvisited:
                if landmark in self.landmarks:
                    landmark_coords = self.landmarks[landmark]['coordinates']
                    distance = self.calculate_distance(current_point, landmark_coords)
                    if distance < min_distance:
                        min_distance = distance
                        nearest = landmark
            
            if nearest:
                route.append(nearest)
                current_point = self.landmarks[nearest]['coordinates']
                unvisited.remove(nearest)
        
        return route



