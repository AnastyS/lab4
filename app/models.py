# Импорт модуля models из библиотеки Django
from django.db import models
# Определение класса, который наследует модель Django Model
class Student(models.Model):
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=100)
    grade = models.IntegerField()

    # Определение метода __str__, который будет использоваться для представления экземпляров модели в виде строки
    def __str__(self):
        return self.name