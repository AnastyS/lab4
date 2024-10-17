# Импорт модуля models из библиотеки Django
from django.db import models
from django.core.exceptions import ValidationError
# Определение класса, который наследует модель Django Model
class Student(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    grade = models.IntegerField()

    def clean(self):
        # Проверка, что оценка находится в диапазоне от 2 до 5
        if self.grade < 2 or self.grade > 5:
            raise ValidationError('Оценка должна быть в диапазоне от 2 до 5.')

    # Определение метода __str__, который будет использоваться для представления экземпляров модели в виде строки
    def __str__(self):
        return self.name