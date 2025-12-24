"""Тесты для моделей данных FitTrack."""

import unittest
from datetime import date, time
from unittest.mock import patch

from fit_track_bot.models import (
    UserProfile,
    Exercise,
    Workout,
    NutritionGoal,
    ValidationError,
    FitTrackError,
)


class TestUserProfile(unittest.TestCase):
    """Тесты для класса UserProfile."""
    
    def test_valid_profile_creation(self):
        """Тест создания корректного профиля."""
        profile = UserProfile(
            gender='мужской',
            age=25,
            height=180.5,
            weight=75.0,
            goal='похудение',
            activity_type='средняя'
        )
        
        self.assertEqual(profile.gender, 'мужской')
        self.assertEqual(profile.age, 25)
        self.assertEqual(profile.height, 180.5)
        self.assertEqual(profile.weight, 75.0)
        self.assertEqual(profile.goal, 'похудение')
        self.assertEqual(profile.activity_type, 'средняя')
    
    def test_invalid_gender(self):
        """Тест создания профиля с некорректным полом."""
        with self.assertRaises(ValidationError) as context:
            UserProfile(
                gender='неизвестный',
                age=25,
                height=180.5,
                weight=75.0,
                goal='похудение',
                activity_type='средняя'
            )
        
        self.assertIn('Некорректный пол', str(context.exception))
    
    def test_invalid_age(self):
        """Тест создания профиля с некорректным возрастом."""
        with self.assertRaises(ValidationError):
            UserProfile(
                gender='мужской',
                age=150,
                height=180.5,
                weight=75.0,
                goal='похудение',
                activity_type='средняя'
            )
    
    def test_invalid_height(self):
        """Тест создания профиля с некорректным ростом."""
        with self.assertRaises(ValidationError):
            UserProfile(
                gender='мужской',
                age=25,
                height=300,
                weight=75.0,
                goal='похудение',
                activity_type='средняя'
            )
    
    def test_calculate_bmi(self):
        """Тест расчета BMI."""
        profile = UserProfile(
            gender='мужской',
            age=25,
            height=180.0,
            weight=72.0,
            goal='похудение',
            activity_type='средняя'
        )
        
        bmi = profile.calculate_bmi()
        expected_bmi = 72.0 / ((180.0 / 100) ** 2)
        self.assertAlmostEqual(bmi, expected_bmi, places=2)
    
    def test_get_bmi_category(self):
        """Тест получения категории BMI."""
        test_cases = [
            (16.0, 'Недостаточный вес'),
            (22.0, 'Нормальный вес'),
            (27.0, 'Избыточный вес'),
            (32.0, 'Ожирение'),
        ]
        
        for bmi_value, expected_category in test_cases:
            with patch.object(UserProfile, 'calculate_bmi', return_value=bmi_value):
                profile = UserProfile(
                    gender='мужской',
                    age=25,
                    height=180.0,
                    weight=72.0,
                    goal='похудение',
                    activity_type='средняя'
                )
                
                category = profile.get_bmi_category()
                self.assertEqual(category, expected_category)


class TestExercise(unittest.TestCase):
    """Тесты для класса Exercise."""
    
    def test_valid_exercise_creation(self):
        """Тест создания корректного упражнения."""
        exercise = Exercise(
            name='Приседания',
            sets=4,
            reps_per_set=10,
            weight=60.0
        )
        
        self.assertEqual(exercise.name, 'Приседания')
        self.assertEqual(exercise.sets, 4)
        self.assertEqual(exercise.reps_per_set, 10)
        self.assertEqual(exercise.weight, 60.0)
    
    def test_invalid_sets(self):
        """Тест создания упражнения с некорректным количеством подходов."""
        with self.assertRaises(ValidationError):
            Exercise(
                name='Приседания',
                sets=0,
                reps_per_set=10,
                weight=60.0
            )
    
    def test_invalid_reps(self):
        """Тест создания упражнения с некорректным количеством повторений."""
        with self.assertRaises(ValidationError):
            Exercise(
                name='Приседания',
                sets=4,
                reps_per_set=0,
                weight=60.0
            )
    
    def test_calculate_volume(self):
        """Тест расчета объема упражнения."""
        exercise = Exercise(
            name='Жим лежа',
            sets=3,
            reps_per_set=8,
            weight=80.0
        )
        
        volume = exercise.calculate_volume()
        expected_volume = 3 * 8 * 80.0
        self.assertEqual(volume, expected_volume)


class TestWorkout(unittest.TestCase):
    """Тесты для класса Workout."""
    
    def test_valid_workout_creation(self):
        """Тест создания корректной тренировки."""
        workout = Workout(
            date=date(2025, 12, 15),
            duration=time(1, 30)
        )
        
        self.assertEqual(workout.date, date(2025, 12, 15))
        self.assertEqual(workout.duration, time(1, 30))
        self.assertEqual(len(workout.exercises), 0)
    
    def test_add_exercise(self):
        """Тест добавления упражнения к тренировке."""
        workout = Workout(
            date=date(2025, 12, 15),
            duration=time(1, 30)
        )
        
        exercise = Exercise(
            name='Приседания',
            sets=4,
            reps_per_set=10,
            weight=60.0
        )
        
        workout.add_exercise(exercise)
        self.assertEqual(len(workout.exercises), 1)
        self.assertEqual(workout.exercises[0].name, 'Приседания')
    
    def test_calculate_total_volume(self):
        """Тест расчета общего объема тренировки."""
        workout = Workout(
            date=date(2025, 12, 15),
            duration=time(1, 30)
        )
        
        exercises = [
            Exercise(name='Приседания', sets=4, reps_per_set=10, weight=60.0),
            Exercise(name='Жим лежа', sets=3, reps_per_set=8, weight=80.0),
        ]
        
        for exercise in exercises:
            workout.add_exercise(exercise)
        
        total_volume = workout.calculate_total_volume()
        expected_volume = (4 * 10 * 60.0) + (3 * 8 * 80.0)
        self.assertEqual(total_volume, expected_volume)
    
    def test_get_exercise_count(self):
        """Тест получения количества упражнений."""
        workout = Workout(
            date=date(2025, 12, 15),
            duration=time(1, 30)
        )
        
        self.assertEqual(workout.get_exercise_count(), 0)
        
        workout.add_exercise(
            Exercise(name='Приседания', sets=4, reps_per_set=10, weight=60.0)
        )
        
        self.assertEqual(workout.get_exercise_count(), 1)


class TestNutritionGoal(unittest.TestCase):
    """Тесты для класса NutritionGoal."""
    
    def test_valid_nutrition_goal_creation(self):
        """Тест создания корректной цели питания."""
        goal = NutritionGoal(
            goal_type='похудение',
            calories=1800.0,
            protein=120.0,
            fat=50.0,
            carbs=180.0
        )
        
        self.assertEqual(goal.goal_type, 'похудение')
        self.assertEqual(goal.calories, 1800.0)
        self.assertEqual(goal.protein, 120.0)
        self.assertEqual(goal.fat, 50.0)
        self.assertEqual(goal.carbs, 180.0)
    
    def test_invalid_goal_type(self):
        """Тест создания цели с некорректным типом."""
        with self.assertRaises(ValidationError):
            NutritionGoal(
                goal_type='неизвестная',
                calories=1800.0,
                protein=120.0,
                fat=50.0,
                carbs=180.0
            )
    
    def test_invalid_calories(self):
        """Тест создания цели с некорректным количеством калорий."""
        with self.assertRaises(ValidationError):
            NutritionGoal(
                goal_type='похудение',
                calories=10000.0,
                protein=120.0,
                fat=50.0,
                carbs=180.0
            )
    
    def test_calculate_macro_calories(self):
        """Тест расчета калорий из макронутриентов."""
        goal = NutritionGoal(
            goal_type='похудение',
            calories=1800.0,
            protein=120.0,
            fat=50.0,
            carbs=180.0
        )
        
        protein_calories = goal.calculate_protein_calories()
        fat_calories = goal.calculate_fat_calories()
        carbs_calories = goal.calculate_carbs_calories()
        
        self.assertEqual(protein_calories, 120.0 * 4)
        self.assertEqual(fat_calories, 50.0 * 9)
        self.assertEqual(carbs_calories, 180.0 * 4)
    
    def test_calculate_total_calories_from_macros(self):
        """Тест расчета общих калорий из макронутриентов."""
        goal = NutritionGoal(
            goal_type='похудение',
            calories=1800.0,
            protein=120.0,
            fat=50.0,
            carbs=180.0
        )
        
        total = goal.calculate_total_calories_from_macros()
        expected_total = (120.0 * 4) + (50.0 * 9) + (180.0 * 4)
        self.assertEqual(total, expected_total)


if __name__ == '__main__':
    unittest.main()
