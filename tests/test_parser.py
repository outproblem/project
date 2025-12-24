"""Модуль тестирования парсера объектов."""

import unittest
from datetime import date, time

from fit_track_bot.parser import ObjectParser


class TestObjectParser(unittest.TestCase):
    """Тесты для класса ObjectParser."""

    def test_parse_string_value(self) -> None:
        """Тест парсинга строковых значений."""
        self.assertEqual(ObjectParser.parse_value('"привет"'), 'привет')
        self.assertEqual(ObjectParser.parse_value('"пример строки"'), 'пример строки')

    def test_parse_int_value(self) -> None:
        """Тест парсинга целых чисел."""
        self.assertEqual(ObjectParser.parse_value('42'), 42)
        self.assertEqual(ObjectParser.parse_value('-10'), -10)

    def test_parse_float_value(self) -> None:
        """Тест парсинга дробных чисел."""
        self.assertEqual(ObjectParser.parse_value('3.14'), 3.14)
        self.assertEqual(ObjectParser.parse_value('-2.5'), -2.5)

    def test_parse_date_value(self) -> None:
        """Тест парсинга дат."""
        expected_date = date(2025, 12, 15)
        self.assertEqual(ObjectParser.parse_value('2025.12.15'), expected_date)

    def test_parse_time_value(self) -> None:
        """Тест парсинга времени."""
        expected_time = time(14, 30)
        self.assertEqual(ObjectParser.parse_value('14:30'), expected_time)

    def test_parse_object(self) -> None:
        """Тест полного парсинга объекта."""
        test_str = 'UserProfile gender "мужской" age 25 height 180.5'
        result = ObjectParser.parse_object(test_str)

        self.assertEqual(result['type'], 'UserProfile')
        self.assertEqual(result['properties']['gender'], 'мужской')
        self.assertEqual(result['properties']['age'], 25)
        self.assertEqual(result['properties']['height'], 180.5)

    def test_parse_object_invalid_format(self) -> None:
        """Тест парсинга объекта с некорректным форматом."""
        with self.assertRaises(ValueError):
            ObjectParser.parse_object('UserProfile gender')

    def test_parse_object_unpaired_key_value(self) -> None:
        """Тест парсинга объекта с непарным ключом-значением."""
        with self.assertRaises(ValueError):
            ObjectParser.parse_object('UserProfile gender "мужской" age')


if __name__ == '__main__':
    unittest.main()
