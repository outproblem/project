"""Основной модуль запуска приложения FitTrack с обработкой ошибок.

Этот модуль демонстрирует работу парсера объектов и запускает Telegram бота,
включая обработку различных сценариев ошибок.
"""

import os
import sys

from fit_track_bot.bot import FitTrackBot
from fit_track_bot.parser import create_object_from_string, ParseError, ValidationError


def demonstrate_correct_cases() -> None:
    """Демонстрирует корректные случаи использования."""
    print('=== КОРРЕКТНЫЕ СЛУЧАИ ===\n')
    
    correct_examples = [
        (
            'UserProfile пол "мужской" age 25 height 180.5 weight 75.0 '
            'goal "похудение" activity_type "средняя"',
            'Профиль пользователя (корректный)',
        ),
        (
            'Exercise name "Приседания" sets 4 reps_per_set 10 weight 60.0',
            'Упражнение (корректное)',
        ),
        (
            'Workout date 2025.12.15 duration 01:30',
            'Тренировка (корректная)',
        ),
        (
            'NutritionGoal goal_type "похудение" calories 1800.0 protein 120.0 '
            'fat 50.0 carbs 180.0',
            'Цель питания (корректная)',
        ),
    ]
    
    for example_str, description in correct_examples:
        print(f'\n{description}:')
        print(f'Входная строка: {example_str}')
        try:
            obj = create_object_from_string(example_str)
            print(f'✅ Объект успешно создан: {type(obj).__name__}')
            
            # Демонстрация методов объектов
            if hasattr(obj, 'calculate_bmi'):
                bmi = obj.calculate_bmi()
                print(f'   BMI: {bmi:.1f}')
            
        except (ParseError, ValidationError) as error:
            print(f'❌ Ошибка: {error}')
        except Exception as error:
            print(f'❌ Неожиданная ошибка: {error}')


def demonstrate_error_cases() -> None:
    """Демонстрирует обработку ошибок."""
    print('\n\n=== ОБРАБОТКА ОШИБОК ===\n')
    
    error_cases = [
        (
            '',
            'Пустая строка',
        ),
        (
            'UserProfile',
            'Неполная строка (только тип)',
        ),
        (
            'UserProfile пол',
            'Неполная строка (непарные ключ-значение)',
        ),
        (
            'UserProfile пол "мужской" age "двадцать пять"',
            'Некорректный тип значения (строка вместо числа)',
        ),
        (
            'UserProfile пол "мужской" age 25 пол "женский"',
            'Дублирующиеся свойства',
        ),
        (
            'UserProfile пол "мужской" age 150 height 180.5 weight 75.0 '
            'goal "похудение" activity_type "средняя"',
            'Некорректные данные (возраст 150 лет)',
        ),
        (
            'UnknownType prop1 "value1" prop2 123',
            'Неизвестный тип объекта',
        ),
        (
            'UserProfile пол мужской age 25',
            'Строка без кавычек',
        ),
        (
            'UserProfile пол "мужской" age 25 height "сто восемьдесят"',
            'Некорректный тип (строка вместо числа)',
        ),
        (
            'Workout date 2025.13.45 duration 25:61',
            'Некорректная дата и время',
        ),
    ]
    
    for example_str, description in error_cases:
        print(f'\n{description}:')
        print(f'Входная строка: {example_str}')
        try:
            obj = create_object_from_string(example_str)
            print(f'✅ Объект создан: {type(obj).__name__}')
        except ParseError as error:
            print(f'❌ Ошибка парсинга: {error}')
        except ValidationError as error:
            print(f'❌ Ошибка валидации: {error}')
        except Exception as error:
            print(f'❌ Неожиданная ошибка: {type(error).__name__}: {error}')


def demonstrate_object_methods() -> None:
    """Демонстрирует методы созданных объектов."""
    print('\n\n=== МЕТОДЫ ОБЪЕКТОВ ===\n')
    
    # Создаем тестовые объекты
    test_cases = [
        (
            'UserProfile пол "мужской" age 25 height 180.5 weight 75.0 '
            'goal "похудение" activity_type "средняя"',
            'UserProfile',
        ),
        (
            'Exercise name "Жим лежа" sets 3 reps_per_set 10 weight 80.0',
            'Exercise',
        ),
        (
            'NutritionGoal goal_type "похудение" calories 1800.0 protein 120.0 '
            'fat 50.0 carbs 180.0',
            'NutritionGoal',
        ),
    ]
    
    for example_str, expected_type in test_cases:
        try:
            obj = create_object_from_string(example_str)
            print(f'\n{type(obj).__name__}:')
            
            # Демонстрация методов в зависимости от типа
            if isinstance(obj, type.__getattr__('UserProfile')):
                print(f'  • BMI: {obj.calculate_bmi():.1f}')
                print(f'  • Категория BMI: {obj.get_bmi_category()}')
                
            elif isinstance(obj, type.__getattr__('Exercise')):
                print(f'  • Объем: {obj.calculate_volume():.1f}')
                print(f'  • Строковое представление: {obj}')
                
            elif isinstance(obj, type.__getattr__('NutritionGoal')):
                print(f'  • Калории из белка: {obj.calculate_protein_calories():.1f}')
                print(f'  • Калории из жиров: {obj.calculate_fat_calories():.1f}')
                print(f'  • Калории из углеводов: {obj.calculate_carbs_calories():.1f}')
                total = obj.calculate_total_calories_from_macros()
                print(f'  • Всего калорий из макронутриентов: {total:.1f}')
                
        except Exception as error:
            print(f'❌ Ошибка: {error}')


def run_bot() -> None:
    """Запускает Telegram бота."""
    bot_token = '8460881839:AAGK_Z8hKunAqgnLMCm3NKoZIVpkF5GsMFQ'
    
    if not bot_token:
        print('\n=== ТЕЛЕГРАМ БОТ ===')
        print('Telegram бот не запущен. Для запуска:')
        print('1. Укажите TELEGRAM_BOT_TOKEN в переменных окружения')
        print('2. Получите токен у @BotFather')
        print('3. Пример: export TELEGRAM_BOT_TOKEN="ваш_токен"')
        return
    
    print('\n=== ЗАПУСК ТЕЛЕГРАМ БОТА ===')
    
    try:
        bot = FitTrackBot(bot_token)
        print('✅ Бот инициализирован успешно')
        print('🚀 Запуск бота...')
        print('📱 Перейдите в Telegram и найдите вашего бота')
        print('⏳ Бот работает (для остановки нажмите Ctrl+C)')
        
        bot.run()
        
    except KeyboardInterrupt:
        print('\n🛑 Бот остановлен пользователем')
    except Exception as error:
        print(f'\n❌ Критическая ошибка при запуске бота: {error}')
        sys.exit(1)


def main() -> None:
    """Основная функция запуска приложения."""
    print('=' * 60)
    print('FIT TRACKER - Демонстрация работы с объектами и обработки ошибок')
    print('=' * 60)
    
    # Демонстрация работы
    demonstrate_correct_cases()
    demonstrate_error_cases()
    demonstrate_object_methods()
    
    # Запуск бота
    run_bot()


if __name__ == '__main__':
    main()
