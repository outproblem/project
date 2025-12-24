"""Парсер для создания объектов из текстовых строк с обработкой ошибок.

Этот модуль предоставляет функциональность для парсинга строк
и создания объектов на основе текстового описания с валидацией.
"""

import re
from datetime import date, time
from typing import Any, Dict, Type

from .models import (
    UserProfile,
    Workout,
    NutritionGoal,
    Exercise,
    FitTrackError,
    ValidationError,
)


class ParseError(FitTrackError):
    """Ошибка парсинга строки."""
    pass


class ObjectParser:
    """Парсер для создания объектов из текстовых строк."""
    
    # Регулярные выражения для определения типов данных
    DATE_PATTERN = re.compile(r'^\d{4}\.\d{2}\.\d{2}$')
    TIME_PATTERN = re.compile(r'^\d{2}:\d{2}$')
    INT_PATTERN = re.compile(r'^-?\d+$')
    FLOAT_PATTERN = re.compile(r'^-?\d+\.\d+$')
    QUOTED_STRING_PATTERN = re.compile(r'^".*"$')
    
    # Маппинг русскоязычных ключей на английские
    RUSSIAN_TO_ENGLISH_MAP = {
        # UserProfile
        'пол': 'gender',
        'гендер': 'gender',
        'возраст': 'age',
        'рост': 'height',
        'вес': 'weight',
        'цель': 'goal',
        'тип_активности': 'activity_type',
        'активность': 'activity_type',
        'уровень_активности': 'activity_type',
        
        # Exercise
        'название': 'name',
        'имя': 'name',
        'подходы': 'sets',
        'повторения': 'reps_per_set',
        'повторы': 'reps_per_set',
        'повторений': 'reps_per_set',
        'вес': 'weight',
        'масса': 'weight',
        'примечания': 'notes',
        
        # Workout
        'дата': 'date',
        'длительность': 'duration',
        'продолжительность': 'duration',
        'упражнения': 'exercises',
        'комментарии': 'notes',
        
        # NutritionGoal
        'тип_цели': 'goal_type',
        'калории': 'calories',
        'белок': 'protein',
        'протеин': 'protein',
        'жиры': 'fat',
        'углеводы': 'carbs',
        'карбс': 'carbs',
    }
    
    @staticmethod
    def _translate_key(key: str) -> str:
        """Переводит русскоязычный ключ на английский.
        
        Args:
            key: Ключ для перевода.
            
        Returns:
            Переведенный ключ или исходный, если перевод не найден.
        """
        # Приводим к нижнему регистру и заменяем пробелы на подчеркивания
        normalized_key = key.lower().replace(' ', '_')
        return ObjectParser.RUSSIAN_TO_ENGLISH_MAP.get(normalized_key, key)
    
    @staticmethod
    def _is_quoted_string(value_str: str) -> bool:
        """Проверяет, является ли строка строкой в кавычках."""
        return bool(ObjectParser.QUOTED_STRING_PATTERN.match(value_str))
    
    @staticmethod
    def _parse_quoted_string(value_str: str) -> str:
        """Извлекает строку из кавычек."""
        return value_str[1:-1]
    
    @staticmethod
    def _parse_date(value_str: str) -> date:
        """Парсит дату из строки формата гггг.мм.дд."""
        try:
            year, month, day = map(int, value_str.split('.'))
            return date(year, month, day)
        except (ValueError, TypeError) as error:
            raise ParseError(f'Некорректный формат даты: {value_str}') from error
    
    @staticmethod
    def _parse_time(value_str: str) -> time:
        """Парсит время из строки формата чч:мм."""
        try:
            hours, minutes = map(int, value_str.split(':'))
            if not (0 <= hours <= 23) or not (0 <= minutes <= 59):
                raise ValueError('Некорректное время')
            return time(hours, minutes)
        except (ValueError, TypeError) as error:
            raise ParseError(f'Некорректный формат времени: {value_str}') from error
    
    @staticmethod
    def parse_value(value_str: str) -> Any:
        """Парсит значение в соответствующий тип данных.
        
        Raises:
            ParseError: Если значение не может быть распарсено.
        """
        try:
            if ObjectParser.DATE_PATTERN.match(value_str):
                return ObjectParser._parse_date(value_str)
            if ObjectParser.TIME_PATTERN.match(value_str):
                return ObjectParser._parse_time(value_str)
            if ObjectParser._is_quoted_string(value_str):
                return ObjectParser._parse_quoted_string(value_str)
            if ObjectParser.INT_PATTERN.match(value_str):
                return int(value_str)
            if ObjectParser.FLOAT_PATTERN.match(value_str):
                return float(value_str)
            return value_str
        except (ValueError, TypeError) as error:
            raise ParseError(f'Не удалось распарсить значение: {value_str}') from error
    
    @staticmethod
    def _tokenize_string(object_str: str) -> list:
        """Разбивает строку на токены с учетом кавычек.
        
        Raises:
            ParseError: Если некорректное использование кавычек.
        """
        if not object_str.strip():
            raise ParseError('Пустая строка')
        
        tokens = []
        current_token = ''
        in_quotes = False
        
        for i, char in enumerate(object_str):
            if char == '"':
                in_quotes = not in_quotes
                current_token += char
            elif char == ' ' and not in_quotes:
                if current_token:
                    tokens.append(current_token)
                    current_token = ''
            else:
                current_token += char
        
        if in_quotes:
            raise ParseError('Незакрытые кавычки в строке')
        
        if current_token:
            tokens.append(current_token)
        
        return tokens
    
    @staticmethod
    def validate_required_properties(
        object_type: str,
        properties: Dict[str, Any],
        required: Dict[str, Type]
    ) -> None:
        """Проверяет наличие обязательных свойств.
        
        Args:
            object_type: Тип объекта.
            properties: Словарь свойств.
            required: Словарь обязательных свойств и их типов.
            
        Raises:
            ParseError: Если отсутствуют обязательные свойства.
        """
        missing_properties = []
        type_errors = []
        
        for prop_name, prop_type in required.items():
            if prop_name not in properties:
                missing_properties.append(prop_name)
            elif not isinstance(properties[prop_name], prop_type):
                type_errors.append(
                    f'{prop_name}: ожидался {prop_type.__name__}, '
                    f'получен {type(properties[prop_name]).__name__}'
                )
        
        error_messages = []
        if missing_properties:
            error_messages.append(
                f'Отсутствуют обязательные свойства: {", ".join(missing_properties)}'
            )
        if type_errors:
            error_messages.append(
                f'Ошибки типов: {"; ".join(type_errors)}'
            )
        
        if error_messages:
            raise ParseError(f'Ошибка валидации {object_type}: {". ".join(error_messages)}')
    
    @staticmethod
    def parse_object(object_str: str) -> Dict[str, Any]:
        """Парсит строку с описанием объекта и возвращает словарь свойств.
        
        Raises:
            ParseError: Если строка имеет некорректный формат.
        """
        try:
            tokens = ObjectParser._tokenize_string(object_str)
            
            if len(tokens) < 3:
                raise ParseError(
                    'Недостаточно данных для создания объекта. '
                    'Минимум: тип объекта + 1 свойство + 1 значение'
                )
            
            if len(tokens) % 2 == 0:
                raise ParseError(
                    'Некорректное количество токенов. '
                    'Ожидается нечетное количество: тип объекта + пары ключ-значение'
                )
            
            object_type = tokens[0]
            properties = {}
            
            for i in range(1, len(tokens), 2):
                if i + 1 >= len(tokens):
                    raise ParseError(f'Непарный ключ-значение для ключа: {tokens[i]}')
                
                key = ObjectParser._translate_key(tokens[i])
                value_str = tokens[i + 1]
                
                if key in properties:
                    raise ParseError(f'Дублирующееся свойство: {tokens[i]} (переведено как: {key})')
                
                properties[key] = ObjectParser.parse_value(value_str)
            
            # Проверка обязательных свойств для известных типов объектов
            required_properties = {
                'UserProfile': {
                    'gender': str,
                    'age': int,
                    'height': float,
                    'weight': float,
                    'goal': str,
                    'activity_type': str,
                },
                'Exercise': {
                    'name': str,
                    'sets': int,
                    'reps_per_set': int,
                    'weight': float,
                },
                'Workout': {
                    'date': date,
                    'duration': time,
                },
                'NutritionGoal': {
                    'goal_type': str,
                    'calories': float,
                    'protein': float,
                    'fat': float,
                    'carbs': float,
                },
            }
            
            if object_type in required_properties:
                ObjectParser.validate_required_properties(
                    object_type,
                    properties,
                    required_properties[object_type]
                )
            
            return {
                'type': object_type,
                'properties': properties,
            }
            
        except ParseError:
            raise
        except Exception as error:
            raise ParseError(f'Неожиданная ошибка при парсинге: {str(error)}') from error


class ObjectFactory:
    """Фабрика для создания объектов на основе распарсенных данных."""
    
    # Маппинг типов объектов на классы
    OBJECT_CLASSES = {
        'UserProfile': UserProfile,
        'Exercise': Exercise,
        'Workout': Workout,
        'NutritionGoal': NutritionGoal,
    }
    
    @staticmethod
    def create_object(parsed_data: Dict[str, Any]) -> Any:
        """Создает объект на основе распарсенных данных.
        
        Args:
            parsed_data: Словарь с распарсенными данными.
            
        Returns:
            Созданный объект.
            
        Raises:
            ParseError: Если тип объекта неизвестен.
            ValidationError: Если данные объекта невалидны.
        """
        object_type = parsed_data['type']
        properties = parsed_data['properties']
        
        if object_type not in ObjectFactory.OBJECT_CLASSES:
            raise ParseError(f'Неизвестный тип объекта: {object_type}')
        
        try:
            object_class = ObjectFactory.OBJECT_CLASSES[object_type]
            return object_class(**properties)
        except ValidationError:
            raise
        except TypeError as error:
            raise ParseError(
                f'Ошибка при создании объекта {object_type}: {str(error)}'
            ) from error


def create_object_from_string(object_str: str) -> Any:
    """Создает объект на основе строки с описанием.
    
    Args:
        object_str: Строка с описанием объекта.
        
    Returns:
        Созданный объект соответствующего типа.
        
    Raises:
        ParseError: Если возникает ошибка парсинга.
        ValidationError: Если данные объекта невалидны.
    """
    try:
        parsed_data = ObjectParser.parse_object(object_str)
        return ObjectFactory.create_object(parsed_data)
    except (ParseError, ValidationError):
        raise
    except Exception as error:
        raise ParseError(f'Неожиданная ошибка: {str(error)}') from error