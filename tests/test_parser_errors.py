"""Тесты обработки ошибок парсера."""

import unittest
from datetime import date, time

from fit_track_bot.parser import (
    ObjectParser,
    ObjectFactory,
    create_object_from_string,
    ParseError,
)
from fit_track_bot.models import ValidationError


class TestParserErrors(unittest.TestCase):
    """Тесты обработки ошибок парсера."""
    
    def test_empty_string(self):
        """Тест пустой строки."""
        with self.assertRaises(ParseError) as context:
            ObjectParser.parse_object('')
        
        self.assertIn('Пустая строка', str(context.exception))
    
    def test_incomplete_string(self):
        """Тест неполной строки."""
        with self.assertRaises(ParseError) as context:
            ObjectParser.parse_object('UserProfile')
        
        self.assertIn('Недостаточно данных', str(context.exception))
    
    def test_unpaired_key_value(self):
        """Тест непарного ключ-значения."""
        with self.assertRaises(ParseError) as context:
            ObjectParser.parse_object('UserProfile gender')
        
        self.assertIn('Непарный ключ-значение', str(context.exception))
    
    def test_duplicate_properties(self):
        """Тест дублирующихся свойств."""
        with self.assertRaises(ParseError) as context:
            ObjectParser.parse_object('UserProfile gender "мужской" gender "женский"')
        
        self.assertIn('Дублирующееся свойство', str(context.exception))
    
    def test_invalid_date_format(self):
        """Тест некорректного формата даты."""
        with self.assertRaises(ParseError):
            ObjectParser.parse_value('2025-12-15')
    
    def test_invalid_time_format(self):
        """Тест некорректного формата времени."""
        with self.assertRaises(ParseError):
            ObjectParser.parse_value('25:61')
    
    def test_missing_required_properties(self):
        """Тест отсутствия обязательных свойств."""
        test_str = 'UserProfile gender "мужской" age 25'
        parsed = ObjectParser.parse_object(test_str)
        
        with self.assertRaises(ParseError) as context:
            ObjectFactory.create_object(parsed)
        
        self.assertIn('Отсутствуют обязательные свойства', str(context.exception))
    
    def test_wrong_property_type(self):
        """Тест некорректного типа свойства."""
        test_str = 'UserProfile gender "мужской" age "двадцать пять" height 180.5'
        parsed = ObjectParser.parse_object(test_str)
        
        with self.assertRaises(ParseError) as context:
            ObjectFactory.create_object(parsed)
        
        self.assertIn('Ошибки типов', str(context.exception))
    
    def test_unknown_object_type(self):
        """Тест неизвестного типа объекта."""
        test_str = 'UnknownType prop1 "value1" prop2 123'
        parsed = ObjectParser.parse_object(test_str)
        
        with self.assertRaises(ParseError) as context:
            ObjectFactory.create_object(parsed)
        
        self.assertIn('Неизвестный тип объекта', str(context.exception))
    
    def test_unclosed_quotes(self):
        """Тест незакрытых кавычек."""
        with self.assertRaises(ParseError) as context:
            ObjectParser.parse_object('UserProfile gender "мужской')
        
        self.assertIn('Незакрытые кавычки', str(context.exception))
    
    def test_create_object_validation_error(self):
        """Тест создания объекта с невалидными данными."""
        test_str = 'UserProfile gender "мужской" age 150 height 180.5 weight 75.0 '
        'goal "похудение" activity_type "средняя"'
        
        with self.assertRaises(ValidationError):
            create_object_from_string(test_str)
    
    def test_mixed_error_scenarios(self):
        """Тест смешанных сценариев ошибок."""
        error_cases = [
            ('', 'пустая строка'),
            ('UserProfile gender', 'неполная строка'),
            ('UnknownType x 1', 'неизвестный тип'),
            ('UserProfile gender мужской age 25', 'строка без кавычек'),
        ]
        
        for test_str, description in error_cases:
            with self.subTest(description=description):
                with self.assertRaises((ParseError, ValidationError)):
                    create_object_from_string(test_str)


class TestParserEdgeCases(unittest.TestCase):
    """Тесты граничных случаев парсера."""
    
    def test_special_characters_in_strings(self):
        """Тест специальных символов в строках."""
        test_str = 'UserProfile gender "мужской/женский" age 25 height 180.5 '
        'weight 75.0 goal "похудение/набор" activity_type "средняя-высокая"'
        
        try:
            obj = create_object_from_string(test_str)
            self.assertEqual(obj.gender, 'мужской/женский')
            self.assertEqual(obj.goal, 'похудение/набор')
            self.assertEqual(obj.activity_type, 'средняя-высокая')
        except (ParseError, ValidationError):
            self.fail('Не удалось распарсить строку со специальными символами')
    
    def test_decimal_values(self):
        """Тест десятичных значений."""
        test_str = 'Exercise name "Жим" sets 3 reps_per_set 8 weight 67.5'
        
        try:
            obj = create_object_from_string(test_str)
            self.assertEqual(obj.weight, 67.5)
        except (ParseError, ValidationError):
            self.fail('Не удалось распарсить десятичные значения')
    
    def test_negative_values(self):
        """Тест отрицательных значений."""
        # Отрицательные значения допустимы только в parse_value,
        # но не в реальных объектах (вес не может быть отрицательным)
        value = ObjectParser.parse_value('-10')
        self.assertEqual(value, -10)
    
    def test_very_long_strings(self):
        """Тест очень длинных строк."""
        long_name = '"Очень длинное название упражнения ' + 'очень ' * 10 + '"'
        test_str = f'Exercise name {long_name} sets 3 reps_per_set 10 weight 50.0'
        
        try:
            obj = create_object_from_string(test_str)
            self.assertIn('очень', obj.name)
        except (ParseError, ValidationError):
            self.fail('Не удалось распарсить длинную строку')


if __name__ == '__main__':
    unittest.main()
