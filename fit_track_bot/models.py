"""Модели данных для FitTrack бота.

Этот модуль содержит классы данных, используемые в приложении.
"""

from dataclasses import dataclass, field
from datetime import date, time
from typing import List, Optional, Dict, Any


class FitTrackError(Exception):
    """Базовое исключение для ошибок FitTrack."""
    pass


class ValidationError(FitTrackError):
    """Ошибка валидации данных."""
    pass


@dataclass
class UserProfile:
    """Профиль пользователя."""
    
    пол: str
    age: int
    height: float
    weight: float
    goal: str
    activity_type: str
    
    def __post_init__(self) -> None:
        """Валидация данных после инициализации."""
        self._validate_пол()
        self._validate_age()
        self._validate_height()
        self._validate_weight()
        self._validate_goal()
        self._validate_activity_type()
    
    def _validate_пол(self) -> None:
        """Валидирует пол пользователя."""
        valid_пол = ['мужской', 'женский']
        if self.пол.lower() not in valid_пол:
            raise ValidationError(
                f'Некорректный пол: {self.пол}. Допустимые значения: {valid_пол}'
            )
    
    def _validate_age(self) -> None:
        """Валидирует возраст пользователя."""
        if not (1 <= self.age <= 120):
            raise ValidationError(
                f'Некорректный возраст: {self.age}. Возраст должен быть от 1 до 120 лет'
            )
    
    def _validate_height(self) -> None:
        """Валидирует рост пользователя."""
        if not (50 <= self.height <= 250):
            raise ValidationError(
                f'Некорректный рост: {self.height}. Рост должен быть от 50 до 250 см'
            )
    
    def _validate_weight(self) -> None:
        """Валидирует вес пользователя."""
        if not (20 <= self.weight <= 300):
            raise ValidationError(
                f'Некорректный вес: {self.weight}. Вес должен быть от 20 до 300 кг'
            )
    
    def _validate_goal(self) -> None:
        """Валидирует цель пользователя."""
        valid_goals = ['похудение', 'набор массы', 'поддержание формы', 'рельеф']
        if self.goal.lower() not in valid_goals:
            raise ValidationError(
                f'Некорректная цель: {self.goal}. Допустимые значения: {valid_goals}'
            )
    
    def _validate_activity_type(self) -> None:
        """Валидирует уровень активности."""
        valid_activities = ['низкая', 'средняя', 'высокая', 'очень высокая']
        if self.activity_type.lower() not in valid_activities:
            raise ValidationError(
                f'Некорректный уровень активности: {self.activity_type}. '
                f'Допустимые значения: {valid_activities}'
            )
    
    def calculate_bmi(self) -> float:
        """Рассчитывает индекс массы тела (BMI).
        
        Returns:
            Значение индекса массы тела.
        """
        height_m = self.height / 100
        return self.weight / (height_m ** 2)
    
    def get_bmi_category(self) -> str:
        """Возвращает категорию BMI.
        
        Returns:
            Категория BMI.
        """
        bmi = self.calculate_bmi()
        
        if bmi < 18.5:
            return 'Недостаточный вес'
        elif 18.5 <= bmi < 25:
            return 'Нормальный вес'
        elif 25 <= bmi < 30:
            return 'Избыточный вес'
        else:
            return 'Ожирение'


@dataclass
class Exercise:
    """Упражнение."""
    
    name: str
    sets: int
    reps_per_set: int
    weight: float
    notes: str = ''
    
    def __post_init__(self) -> None:
        """Валидация данных после инициализации."""
        self._validate_sets()
        self._validate_reps()
        self._validate_weight()
    
    def _validate_sets(self) -> None:
        """Валидирует количество подходов."""
        if not (1 <= self.sets <= 20):
            raise ValidationError(
                f'Некорректное количество подходов: {self.sets}. '
                f'Должно быть от 1 до 20'
            )
    
    def _validate_reps(self) -> None:
        """Валидирует количество повторений."""
        if not (1 <= self.reps_per_set <= 100):
            raise ValidationError(
                f'Некорректное количество повторений: {self.reps_per_set}. '
                f'Должно быть от 1 до 100'
            )
    
    def _validate_weight(self) -> None:
        """Валидирует вес."""
        if not (0 <= self.weight <= 1000):
            raise ValidationError(
                f'Некорректный вес: {self.weight}. '
                f'Должен быть от 0 до 1000 кг'
            )
    
    def calculate_volume(self) -> float:
        """Рассчитывает тренировочный объем.
        
        Returns:
            Объем (подходы × повторения × вес).
        """
        return self.sets * self.reps_per_set * self.weight
    
    def __str__(self) -> str:
        """Строковое представление упражнения."""
        return f'{self.name}: {self.sets}×{self.reps_per_set} с весом {self.weight}кг'


@dataclass
class Workout:
    """Тренировка."""
    
    date: date
    duration: time
    exercises: List[Exercise] = field(default_factory=list)
    notes: str = ''
    
    def __post_init__(self) -> None:
        """Валидация данных после инициализации."""
        self._validate_date()
    
    def _validate_date(self) -> None:
        """Валидирует дату тренировки."""
        from datetime import datetime
        if self.date > datetime.now().date():
            raise ValidationError('Дата тренировки не может быть в будущем')
    
    def add_exercise(self, exercise: Exercise) -> None:
        """Добавляет упражнение к тренировке.
        
        Args:
            exercise: Упражнение для добавления.
        """
        self.exercises.append(exercise)
    
    def calculate_total_volume(self) -> float:
        """Рассчитывает общий объем тренировки.
        
        Returns:
            Суммарный объем всех упражнений.
        """
        return sum(exercise.calculate_volume() for exercise in self.exercises)
    
    def get_exercise_count(self) -> int:
        """Возвращает количество упражнений.
        
        Returns:
            Количество упражнений.
        """
        return len(self.exercises)


@dataclass
class NutritionGoal:
    """Цель питания."""
    
    goal_type: str
    calories: float
    protein: float
    fat: float
    carbs: float
    
    def __post_init__(self) -> None:
        """Валидация данных после инициализации."""
        self._validate_goal_type()
        self._validate_calories()
        self._validate_macronutrients()
    
    def _validate_goal_type(self) -> None:
        """Валидирует тип цели."""
        valid_goals = ['похудение', 'поддержание', 'набор массы']
        if self.goal_type.lower() not in valid_goals:
            raise ValidationError(
                f'Некорректный тип цели: {self.goal_type}. '
                f'Допустимые значения: {valid_goals}'
            )
    
    def _validate_calories(self) -> None:
        """Валидирует калории."""
        if not (500 <= self.calories <= 5000):
            raise ValidationError(
                f'Некорректное количество калорий: {self.calories}. '
                f'Должно быть от 500 до 5000 ккал'
            )
    
    def _validate_macronutrients(self) -> None:
        """Валидирует макронутриенты."""
        if not (0 <= self.protein <= 500):
            raise ValidationError(
                f'Некорректное количество белка: {self.protein}. '
                f'Должно быть от 0 до 500 г'
            )
        
        if not (0 <= self.fat <= 200):
            raise ValidationError(
                f'Некорректное количество жиров: {self.fat}. '
                f'Должно быть от 0 до 200 г'
            )
        
        if not (0 <= self.carbs <= 1000):
            raise ValidationError(
                f'Некорректное количество углеводов: {self.carbs}. '
                f'Должно быть от 0 до 1000 г'
            )
    
    def calculate_protein_calories(self) -> float:
        """Рассчитывает калории из белка.
        
        Returns:
            Калории из белка (4 ккал/г).
        """
        return self.protein * 4
    
    def calculate_fat_calories(self) -> float:
        """Рассчитывает калории из жиров.
        
        Returns:
            Калории из жиров (9 ккал/г).
        """
        return self.fat * 9
    
    def calculate_carbs_calories(self) -> float:
        """Рассчитывает калории из углеводов.
        
        Returns:
            Калории из углеводов (4 ккал/г).
        """
        return self.carbs * 4
    
    def calculate_total_calories_from_macros(self) -> float:
        """Рассчитывает общее количество калорий из макронутриентов.
        
        Returns:
            Сумма калорий из всех макронутриентов.
        """
        return (
            self.calculate_protein_calories() +
            self.calculate_fat_calories() +
            self.calculate_carbs_calories()
        )
