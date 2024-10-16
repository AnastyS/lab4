# Импорт модуля admin из библиотеки Django.contrib
from django.contrib import admin
# Импорт модели Student из текущего каталога (".")
from .models import Student
# Регистрация модели Student для административного сайта
admin.site.register(Student)