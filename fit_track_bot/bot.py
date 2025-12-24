"""Telegram-бот для отслеживания тренировок и питания с обработкой ошибок."""

import logging
from typing import Dict, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
)

from .models import (
    UserProfile,
    Workout,
    NutritionGoal,
    Exercise,
    FitTrackError,
    ValidationError,
)
from .parser import create_object_from_string, ParseError


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class BotError(FitTrackError):
    """Ошибка бота."""
    pass


class UserNotFoundError(BotError):
    """Ошибка: пользователь не найден."""
    pass


class FitTrackBot:
    """Telegram-бот для отслеживания тренировок и питания."""
    
    def __init__(self, token: str) -> None:
        """Инициализирует бота.
        
        Args:
            token: Токен Telegram бота.
        """
        self.token = token
        self.application = Application.builder().token(token).build()
        self.user_data: Dict[int, Dict[str, Any]] = {}
        self._setup_handlers()
        logger.info('Бот инициализирован')
    
    def _setup_handlers(self) -> None:
        """Настраивает обработчики команд бота."""
        try:
            handlers = [
                CommandHandler('start', self._handle_start),
                CommandHandler('help', self._handle_help),
                CommandHandler('profile', self._handle_profile),
                CommandHandler('bmi', self._handle_bmi),
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_object_creation),
                CallbackQueryHandler(self._handle_button_click),
            ]
            
            for handler in handlers:
                self.application.add_handler(handler)
            
            logger.info('Обработчики команд настроены')
        except Exception as error:
            logger.error(f'Ошибка при настройке обработчиков: {error}')
            raise BotError('Не удалось настроить обработчики команд') from error
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает команду /start."""
        try:
            welcome_text = self._get_welcome_message()
            await update.message.reply_text(welcome_text)
            logger.info(f'Пользователь {update.effective_user.id} запустил бота')
        except Exception as error:
            logger.error(f'Ошибка при обработке /start: {error}')
            await update.message.reply_text('❌ Произошла ошибка при запуске бота')
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает команду /help."""
        try:
            help_text = self._get_help_message()
            await update.message.reply_text(help_text)
        except Exception as error:
            logger.error(f'Ошибка при обработке /help: {error}')
            await update.message.reply_text('❌ Произошла ошибка при показе справки')
    
    async def _handle_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает команду /profile."""
        try:
            user_id = update.effective_user.id
            if user_id not in self.user_data or 'profile' not in self.user_data[user_id]:
                await update.message.reply_text(
                    '📝 У вас еще нет профиля. Создайте его командой:\n\n'
                    'UserProfile gender "мужской" age 25 height 180.5 weight 75.0 '
                    'goal "похудение" activity_type "средняя"'
                )
                return
            
            profile = self.user_data[user_id]['profile']
            response = self._format_profile_info(profile)
            await update.message.reply_text(response)
        except Exception as error:
            logger.error(f'Ошибка при обработке /profile: {error}')
            await update.message.reply_text('❌ Произошла ошибка при показе профиля')
    
    async def _handle_bmi(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает команду /bmi."""
        try:
            user_id = update.effective_user.id
            if user_id not in self.user_data or 'profile' not in self.user_data[user_id]:
                await update.message.reply_text(
                    '📝 Для расчета BMI нужен профиль. Создайте его командой:\n\n'
                    'UserProfile gender "мужской" age 25 height 180.5 weight 75.0 '
                    'goal "похудение" activity_type "средняя"'
                )
                return
            
            profile = self.user_data[user_id]['profile']
            bmi = profile.calculate_bmi()
            category = profile.get_bmi_category()
            
            response = (
                f'📊 Ваш индекс массы тела (BMI):\n\n'
                f'• BMI: {bmi:.1f}\n'
                f'• Категория: {category}\n\n'
                f'📈 Интерпретация BMI:\n'
                f'< 18.5: Недостаточный вес\n'
                f'18.5-24.9: Нормальный вес\n'
                f'25-29.9: Избыточный вес\n'
                f'≥ 30: Ожирение'
            )
            
            await update.message.reply_text(response)
        except Exception as error:
            logger.error(f'Ошибка при обработке /bmi: {error}')
            await update.message.reply_text('❌ Произошла ошибка при расчете BMI')
    
    async def _handle_object_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает создание объектов из текстовых строк."""
        try:
            user_input = update.message.text
            logger.info(f'Пользователь {update.effective_user.id} отправил: {user_input[:50]}...')
            
            created_object = create_object_from_string(user_input)
            response = self._create_response_for_object(
                created_object, 
                update.effective_user.id
            )
            
            await update.message.reply_text(response)
            logger.info(f'Объект успешно создан: {type(created_object).__name__}')
            
        except ParseError as error:
            error_message = self._create_parse_error_message(error, user_input)
            await update.message.reply_text(error_message)
            logger.warning(f'Ошибка парсинга: {error}')
            
        except ValidationError as error:
            error_message = self._create_validation_error_message(error)
            await update.message.reply_text(error_message)
            logger.warning(f'Ошибка валидации: {error}')
            
        except Exception as error:
            error_message = self._create_unexpected_error_message(error)
            await update.message.reply_text(error_message)
            logger.error(f'Неожиданная ошибка: {error}')
    
    async def _handle_button_click(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает нажатия на кнопки."""
        try:
            query = update.callback_query
            await query.answer()
            
            button_data = query.data
            logger.info(f'Нажата кнопка: {button_data}')
            
            if button_data == 'menu':
                await self._show_main_menu(query)
            elif button_data == 'profile_info':
                await self._show_profile_info(query)
            elif button_data == 'nutrition_info':
                await self._show_nutrition_info(query)
            elif button_data == 'workout_info':
                await self._show_workout_info(query)
            else:
                await query.edit_message_text(
                    '❌ Неизвестная команда. Вернитесь в меню.',
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton('Вернуться в меню', callback_data='menu')
                    ]])
                )
                
        except Exception as error:
            logger.error(f'Ошибка при обработке кнопки: {error}')
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    '❌ Произошла ошибка. Пожалуйста, попробуйте снова.'
                )
    
    async def _show_main_menu(self, query) -> None:
        """Показывает главное меню."""
        try:
            keyboard = [
                [InlineKeyboardButton('👤 Профиль', callback_data='profile_info')],
                [InlineKeyboardButton('🍎 Питание', callback_data='nutrition_info')],
                [InlineKeyboardButton('🏋️ Тренировки', callback_data='workout_info')],
                [InlineKeyboardButton('📊 Прогресс', callback_data='progress')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                '🏋️‍♂️ Главное меню FitTrack:\n\n'
                'Выберите раздел:',
                reply_markup=reply_markup,
            )
        except Exception as error:
            logger.error(f'Ошибка при показе главного меню: {error}')
            raise
    
    async def _show_profile_info(self, query) -> None:
        """Показывает информацию о профиле."""
        try:
            user_id = query.from_user.id
            if user_id not in self.user_data or 'profile' not in self.user_data[user_id]:
                message = (
                    '📝 У вас еще нет профиля.\n\n'
                    'Создайте профиль, отправив сообщение в формате:\n\n'
                    'UserProfile gender "мужской" age 25 height 180.5 weight 75.0 '
                    'goal "похудение" activity_type "средняя"'
                )
            else:
                profile = self.user_data[user_id]['profile']
                message = self._format_profile_info(profile)
            
            keyboard = [[InlineKeyboardButton('Вернуться в меню', callback_data='menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
        except Exception as error:
            logger.error(f'Ошибка при показе информации о профиле: {error}')
            raise
    
    async def _show_nutrition_info(self, query) -> None:
        """Показывает информацию о питании."""
        try:
            message = (
                '🍎 Раздел питания\n\n'
                'Создайте цель питания, отправив сообщение в формате:\n\n'
                'NutritionGoal goal_type "похудение" calories 1800.0 '
                'protein 120.0 fat 50.0 carbs 180.0\n\n'
                'Или выберите готовый план:'
            )
            
            keyboard = [
                [InlineKeyboardButton('Похудение', callback_data='lose_weight')],
                [InlineKeyboardButton('Поддержание формы', callback_data='maintain')],
                [InlineKeyboardButton('Набор массы', callback_data='gain_weight')],
                [InlineKeyboardButton('Вернуться в меню', callback_data='menu')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
        except Exception as error:
            logger.error(f'Ошибка при показе информации о питании: {error}')
            raise
    
    async def _show_workout_info(self, query) -> None:
        """Показывает информацию о тренировках."""
        try:
            message = (
                '🏋️ Раздел тренировок\n\n'
                'Создайте тренировку, отправив сообщение в формате:\n\n'
                'Workout date 2025.12.15 duration 01:30\n\n'
                'Создайте упражнение:\n\n'
                'Exercise name "Приседания" sets 4 reps_per_set 10 weight 60.0'
            )
            
            keyboard = [
                [InlineKeyboardButton('Создать тренировку', callback_data='create_workout')],
                [InlineKeyboardButton('История тренировок', callback_data='workout_history')],
                [InlineKeyboardButton('Вернуться в меню', callback_data='menu')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(message, reply_markup=reply_markup)
        except Exception as error:
            logger.error(f'Ошибка при показе информации о тренировках: {error}')
            raise
    
    def _create_response_for_object(self, obj: Any, user_id: int) -> str:
        """Создает ответное сообщение для созданного объекта."""
        try:
            if isinstance(obj, UserProfile):
                self.user_data[user_id] = {'profile': obj}
                response = self._format_user_profile_response(obj)
            elif isinstance(obj, Exercise):
                response = (
                    f'✅ Упражнение создано!\n\n'
                    f'Название: {obj.name}\n'
                    f'Подходы: {obj.sets}\n'
                    f'Повторений: {obj.reps_per_set}\n'
                    f'Вес: {obj.weight} кг\n'
                    f'Объем: {obj.calculate_volume():.1f}'
                )
            elif isinstance(obj, Workout):
                response = (
                    f'✅ Тренировка создана!\n\n'
                    f'Дата: {obj.date}\n'
                    f'Продолжительность: {obj.duration}\n'
                    f'Упражнений: {obj.get_exercise_count()}'
                )
            elif isinstance(obj, NutritionGoal):
                response = (
                    f'✅ Цель питания создана!\n\n'
                    f'Тип цели: {obj.goal_type}\n'
                    f'Калории: {obj.calories} ккал\n'
                    f'Белок: {obj.protein} г\n'
                    f'Жиры: {obj.fat} г\n'
                    f'Углеводы: {obj.carbs} г'
                )
            else:
                response = f'✅ Объект создан: {type(obj).__name__}'
            
            return response
        except Exception as error:
            logger.error(f'Ошибка при создании ответа для объекта: {error}')
            return '✅ Объект успешно создан'
    
    def _format_user_profile_response(self, profile: UserProfile) -> str:
        """Форматирует информацию о профиле пользователя."""
        bmi = profile.calculate_bmi()
        category = profile.get_bmi_category()
        
        return (
            f'✅ Профиль пользователя создан!\n\n'
            f'📊 Основная информация:\n'
            f'• Пол: {profile.gender}\n'
            f'• Возраст: {profile.age} лет\n'
            f'• Рост: {profile.height} см\n'
            f'• Вес: {profile.weight} кг\n\n'
            f'🎯 Цели:\n'
            f'• Цель: {profile.goal}\n'
            f'• Активность: {profile.activity_type}\n\n'
            f'📈 Индекс массы тела:\n'
            f'• BMI: {bmi:.1f}\n'
            f'• Категория: {category}'
        )
    
    def _format_profile_info(self, profile: UserProfile) -> str:
        """Форматирует полную информацию о профиле."""
        bmi = profile.calculate_bmi()
        category = profile.get_bmi_category()
        
        return (
            f'👤 Ваш профиль:\n\n'
            f'📊 Основная информация:\n'
            f'• Пол: {profile.gender}\n'
            f'• Возраст: {profile.age} лет\n'
            f'• Рост: {profile.height} см\n'
            f'• Вес: {profile.weight} кг\n\n'
            f'🎯 Цели:\n'
            f'• Цель: {profile.goal}\n'
            f'• Уровень активности: {profile.activity_type}\n\n'
            f'📈 Индекс массы тела:\n'
            f'• BMI: {bmi:.1f}\n'
            f'• Категория: {category}\n\n'
            f'💡 Рекомендации:\n'
            f'1. Регулярно обновляйте вес\n'
            f'2. Следите за прогрессом\n'
            f'3. Консультируйтесь с врачом'
        )
    
    def _create_parse_error_message(self, error: ParseError, user_input: str) -> str:
        """Создает сообщение об ошибке парсинга."""
        examples = (
            '\n\n📝 Примеры правильного формата:\n\n'
            'Профиль пользователя:\n'
            'UserProfile gender "мужской" age 25 height 180.5 weight 75.0 '
            'goal "похудение" activity_type "средняя"\n\n'
            'Упражнение:\n'
            'Exercise name "Приседания" sets 4 reps_per_set 10 weight 60.0\n\n'
            'Тренировка:\n'
            'Workout date 2025.12.15 duration 01:30\n\n'
            'Цель питания:\n'
            'NutritionGoal goal_type "похудение" calories 1800.0 '
            'protein 120.0 fat 50.0 carbs 180.0'
        )
        
        return f'❌ Ошибка парсинга: {str(error)}{examples}'
    
    def _create_validation_error_message(self, error: ValidationError) -> str:
        """Создает сообщение об ошибке валидации."""
        return (
            f'❌ Ошибка валидации данных:\n{str(error)}\n\n'
            f'📝 Проверьте введенные данные и попробуйте снова.'
        )
    
    def _create_unexpected_error_message(self, error: Exception) -> str:
        """Создает сообщение о неожиданной ошибке."""
        logger.error(f'Неожиданная ошибка: {error}', exc_info=True)
        return (
            '❌ Произошла непредвиденная ошибка.\n'
            'Пожалуйста, попробуйте снова или свяжитесь с поддержкой.\n\n'
            'Техническая информация:\n'
            f'{type(error).__name__}: {str(error)}'
        )
    
    def _get_welcome_message(self) -> str:
        """Возвращает приветственное сообщение."""
        return (
            '🏋️‍♂️ Добро пожаловать в FitTrack! 🏋️‍♂️\n\n'
            'Я помогу вам отслеживать фитнес-прогресс.\n\n'
            '📋 Доступные команды:\n'
            '/start - Начать работу\n'
            '/help - Справка по командам\n'
            '/profile - Показать профиль\n'
            '/bmi - Рассчитать индекс массы тела\n\n'
            '🛠️ Создание объектов:\n'
            'Отправьте сообщение в формате:\n'
            'ТипОбъекта свойство1 значение1 свойство2 значение2 ...\n\n'
            'Например:\n'
            'UserProfile gender "мужской" age 25 height 180.5 ...'
        )
    
    def _get_help_message(self) -> str:
        """Возвращает сообщение со справкой."""
        return (
            '📚 Справка по FitTrack Bot\n\n'
            '🎯 Поддерживаемые типы объектов:\n\n'
            '1. UserProfile - Профиль пользователя\n'
            '   Обязательные свойства: gender/пол, age/возраст, height/рост, weight/вес, goal/цель, activity_type/активность\n'
            '   Пример (русские ключи): UserProfile пол "мужской" возраст 25 рост 180.5 вес 75.0 '
            'цель "похудение" активность "средняя"\n'
            '   Пример (английские ключи): UserProfile gender "мужской" age 25 height 180.5 weight 75.0 '
            'goal "похудение" activity_type "средняя"\n\n'
            '2. Exercise - Упражнение\n'
            '   Обязательные свойства: name/название, sets/подходы, reps_per_set/повторения, weight/вес\n'
            '   Пример (русские ключи): Exercise название "Приседания" подходы 4 повторения 10 вес 60.0\n'
            '   Пример (английские ключи): Exercise name "Приседания" sets 4 reps_per_set 10 weight 60.0\n\n'
            '3. Workout - Тренировка\n'
            '   Обязательные свойства: date/дата, duration/длительность\n'
            '   Пример (русские ключи): Workout дата 2025.12.15 длительность 01:30\n'
            '   Пример (английские ключи): Workout date 2025.12.15 duration 01:30\n\n'
            '4. NutritionGoal - Цель питания\n'
            '   Обязательные свойства: goal_type/тип_цели, calories/калории, protein/белок, fat/жиры, carbs/углеводы\n'
            '   Пример (русские ключи): NutritionGoal тип_цели "похудение" калории 1800.0 '
            'белок 120.0 жиры 50.0 углеводы 180.0\n'
            '   Пример (английские ключи): NutritionGoal goal_type "похудение" calories 1800.0 '
            'protein 120.0 fat 50.0 carbs 180.0\n\n'
            '📞 Для помощи: /start - главное меню'
        )
    
    def run(self) -> None:
        """Запускает бота."""
        try:
            logger.info('Запуск бота...')
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )
        except Exception as error:
            logger.error(f'Критическая ошибка при запуске бота: {error}')
            raise BotError('Не удалось запустить бота') from error
