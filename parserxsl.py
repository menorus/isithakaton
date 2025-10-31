import re
import os
from typing import  Tuple, Optional
import pandas as pd


class Parser:

    #Загрузка данных из Excel 

    @staticmethod
    def load_landmarks_from_excel(file_path: str = "cultural_objects_mnn.xlsx"):
        try:
            if not os.path.exists(file_path):
                print(f"❌ Файл {file_path} не найден!")
                return Parser.get_default_landmarks()
            
            df = pd.read_excel(file_path)
            landmarks = {}
            
            print("📊 Колонки в файле:", df.columns.tolist())
            
            name_col = None
            coords_col = None
            category_col = None
            rating_col = None
            time_col = None
            description_col = None
            features_col = None
            
            for i, col_name in enumerate(df.columns):
                col_lower = str(col_name).lower()
                if any(keyword in col_lower for keyword in ['название', 'name', 'объект', 'title']):
                    name_col = i
                elif any(keyword in col_lower for keyword in ['координат', 'coord', 'гео', 'point']):
                    coords_col = i
                elif any(keyword in col_lower for keyword in ['категория', 'category', 'тип', 'type']):
                    category_col = i
                elif any(keyword in col_lower for keyword in ['рейтинг', 'rating', 'оценка']):
                    rating_col = i
                elif any(keyword in col_lower for keyword in ['время', 'time', 'продолжительность']):
                    time_col = i
                elif any(keyword in col_lower for keyword in ['описание', 'description', 'информация']):
                    description_col = i
                elif any(keyword in col_lower for keyword in ['особенности', 'features', 'теги', 'tags']):
                    features_col = i
            
            print(f"🔍 Определены колонки: название={name_col}, координаты={coords_col}, категория={category_col}")
            
            for index, row in df.iterrows():
                try:
                    if name_col is None or pd.isna(row.iloc[name_col]):
                        continue
                    
                    name = str(row.iloc[name_col]).strip()
                    if not name or name == 'nan':
                        continue
                    
                    # Обработка координат
                    coords = None
                    if coords_col is not None and len(row) > coords_col:
                        coords_str = str(row.iloc[coords_col])
                        coords = Parser.parse_point_coordinates(coords_str)
                    
                    if not coords:
                        print(f"❌ Не удалось распарсить координаты для {name}")
                        continue
                    
                    # Обработка категории
                    category = "other"
                    if category_col is not None and len(row) > category_col:
                        category_val = row.iloc[category_col]
                        if not pd.isna(category_val):
                            category = str(category_val).strip().lower()
                    
                    # Обработка рейтинга
                    rating = 4.0
                    if rating_col is not None and len(row) > rating_col:
                        try:
                            rating_val = row.iloc[rating_col]
                            if not pd.isna(rating_val):
                                rating = float(rating_val)
                        except:
                            pass
                    
                    # Обработка времени посещения
                    visit_time = 1.0
                    if time_col is not None and len(row) > time_col:
                        try:
                            time_val = row.iloc[time_col]
                            if not pd.isna(time_val):
                                visit_time = float(time_val)/10
                        except:
                            pass
                    
                    # Обработка описания
                    description = ""
                    if description_col is not None and len(row) > description_col:
                        desc_val = row.iloc[description_col]
                        if not pd.isna(desc_val):
                            description = str(desc_val).strip()
                    
                    # Обработка особенностей
                    features = []
                    if features_col is not None and len(row) > features_col:
                        features_val = row.iloc[features_col]
                        if not pd.isna(features_val):
                            features = [f.strip() for f in str(features_val).split(',') if f.strip()]
                    
                    landmarks[name] = {
                        'coordinates': coords,
                        'category': category,
                        'rating': rating,
                        'visit_time': visit_time,
                        'description': description,
                        'features': features,
                        'original_description': description 
                    }
                    
                    print(f"✅ Загружено: {name} - {coords} - категория: {category}")
                    
                except Exception as e:
                    print(f"❌ Ошибка в строке {index}: {e}")
                    continue
            
            print(f"🎯 Итог: загружено {len(landmarks)} достопримечательностей")
            return landmarks
            
        except Exception as e:
            print(f"❌ Критическая ошибка загрузки Excel: {e}")
            return Parser.get_default_landmarks()
   
    @staticmethod
    def parse_point_coordinates(coord_str: str) -> Optional[Tuple[float, float]]:
        #Парсинг координат в формате POINT где долгота первая, широта вторая
        if pd.isna(coord_str) or not coord_str:
            return None
        
        coord_str = str(coord_str).strip()
        
        # Основные форматы для POINT 
        point_formats = [
            r'POINT\s*\(\s*([\d.]+)\s+([\d.]+)\s*\)',  
            r'POINT\(\s*([\d.]+)\s+([\d.]+)\s*\)',     
            r'\(\s*([\d.]+)\s+([\d.]+)\s*\)',        
            r'([\d.]+)\s+([\d.]+)',                    
        ]
        
        for pattern in point_formats:
            match = re.search(pattern, coord_str, re.IGNORECASE)
            if match:
                try:
                    lon = float(match.group(1))  # долгота
                    lat = float(match.group(2))  # широта
                    
                    # Проверяем, что координаты в пределах НН
                    if 43.0 <= lon <= 45.0 and 56.0 <= lat <= 57.0:
                        return (lat, lon)  
                    else:
                        print(f"❌ Координаты вне пределов НН: lon={lon}, lat={lat}")
                        
                except ValueError as e:
                    print(f"❌ Ошибка преобразования чисел: {e}")
                    continue
        
        return None
    
    @staticmethod
    def get_default_landmarks():
        landmarks = {
            "Нижегородский Кремль": {
                'coordinates': (56.3271, 44.0023),
                'category': 'история', 
                'rating': 4.8, 
                'visit_time': 1.5,
                'description': 'Крепость XVI века с 13 башнями, откуда открывается панорамный вид на Волгу и Оку.',
                'features': ['Архитектура', 'История', 'Панорамные виды'],
                'original_description': 'Крепость XVI века с 13 башнями, откуда открывается панорамный вид на Волгу и Оку.'
            },
            "Чкаловская лестница": {
                'coordinates': (56.3300, 44.0125),
                'category': 'архитектура', 
                'rating': 4.5, 
                'visit_time': 0.5,
                'description': 'Одна из самых длинных лестниц в России (560 ступеней).',
                'features': ['Архитектура', 'Фотолокации', 'Панорамные виды'],
                'original_description': 'Одна из самых длинных лестниц в России (560 ступеней).'
            },
            "Большая Покровская улица": {
                'coordinates': (56.3186, 44.0022),
                'category': 'прогулка', 
                'rating': 4.7, 
                'visit_time': 2.0,
                'description': 'Главная пешеходная улица города.',
                'features': ['Шоппинг', 'Кафе', 'Архитектура'],
                'original_description': 'Главная пешеходная улица города.'
            },
            "Рождественская улица": {
                'coordinates': (56.3250, 43.9850),
                'category': 'архитектура', 
                'rating': 4.6, 
                'visit_time': 1.0,
                'description': 'Историческая улица с купеческими особняками.',
                'features': ['Архитектура', 'История', 'Фотолокации'],
                'original_description': 'Историческая улица с купеческими особняками.'
            },
            "Набережная Федоровского": {
                'coordinates': (56.3320, 43.9950),
                'category': 'прогулка', 
                'rating': 4.4, 
                'visit_time': 0.5,
                'description': 'Живописная набережная с видом на Стрелку.',
                'features': ['Панорамные виды', 'Природа', 'Фотолокации'],
                'original_description': 'Живописная набережная с видом на Стрелку.'
            },
            "Парк Победы": {
                'coordinates': (56.3100, 43.9900),
                'category': 'парк', 
                'rating': 4.3, 
                'visit_time': 1.0,
                'description': 'Мемориальный парк с военной техникой.',
                'features': ['История', 'Природа', 'Прогулки'],
                'original_description': 'Мемориальный парк с военной техникой.'
            },
            "Нижегородская ярмарка": {
                'coordinates': (56.3350, 43.9750),
                'category': 'архитектура', 
                'rating': 4.5, 
                'visit_time': 1.0,
                'description': 'Исторический выставочный комплекс.',
                'features': ['Архитектура', 'История', 'Выставки'],
                'original_description': 'Исторический выставочный комплекс.'
            },
            "Собор Александра Невского": {
                'coordinates': (56.3330, 43.9750),
                'category': 'архитектура', 
                'rating': 4.6, 
                'visit_time': 0.5,
                'description': 'Православный собор в Стрелке Оки и Волги.',
                'features': ['Архитектура', 'Религия', 'История'],
                'original_description': 'Православный собор в Стрелке Оки и Волги.'
            }
        }
        
        print(f"✅ Создано {len(landmarks)} тестовых достопримечательностей")
        return landmarks
    
    
    @staticmethod
    def output_lendmarks():
        "Загрузка достопремечательностей"
        LANDMARKS = Parser.load_landmarks_from_excel("cultural_objects_mnn.xlsx")
        if len(LANDMARKS) == 0:
            LANDMARKS = Parser.get_default_landmarks()
        print(f"✅ Загружено {len(LANDMARKS)} достопримечательностей")
        return LANDMARKS
    

