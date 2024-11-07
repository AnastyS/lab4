from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import Student_form
from .models import Student
import os
import xml.etree.ElementTree as ET
import re
from django.db import connection #соединение с бд
from django.shortcuts import get_object_or_404 #получение объекта из бд по критериям
from django.http import JsonResponse #возврат JSON ответов

# Функция сохранения данных в XML файл (не изменялась)
def create_or_update_xml_file(data):
    file_path = "XMLfiles/performance.xml"

    # Проверяем, существует ли файл
    if os.path.exists(file_path):
        # Проверяем, пустой ли файл
        if os.path.getsize(file_path) == 0:
            root = ET.Element("data")  # Создаем корневой элемент, если файл пустой
            tree = ET.ElementTree(root)
        else:
            tree = ET.parse(file_path)  # Загружаем существующий файл
            root = tree.getroot()
    else:
        # Если файла нет, создаём новый корневой элемент
        root = ET.Element("data")
        tree = ET.ElementTree(root)

    # Проверка на наличие дубликатов
    keys = ['name', 'subject', 'grade']
    is_duplicate = any(
        all(existing_entry.find(key).text == str(data[key]) for key in keys)
        for existing_entry in root.findall('entry')
    )

    if not is_duplicate:
        # Добавляем новую запись в XML, если она уникальна
        entry = ET.SubElement(root, "entry")
        for key, value in data.items():
            child = ET.SubElement(entry, key)
            child.text = str(value)

        # Форматируем XML с отступами
        ET.indent(tree, space="  ", level=0)

        # Сохраняем обновлённый XML-файл с отступами
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
        return True
    else:
        return False  # Указывает, что запись дублирующая
    
# Проверка на дубликаты в базе данных
def check_for_duplicates_in_db(cleaned_data):
    return Student.objects.filter(
        name=cleaned_data['name'],
        grade=cleaned_data['grade'],
        subject=cleaned_data['subject'],
    ).exists()

# Основная логика обработки формы
def student_form(request):
    form = Student_form()
    if request.method == 'POST':
        form = Student_form(request.POST)
        if form.is_valid():
           cleaned_data = form.cleaned_data

           if request.POST.get('save_to') == 'database':
               # Сохранение в базу данных
               if check_for_duplicates_in_db(cleaned_data):
                   return render(request, 'student_form.html', {'form': form, 'success': False, 'message': "Дублирующая запись"})
               else:
                form.save()  # Сохранение в базу данных
                return render(request, 'student_form.html', {'form': form, 'success': True, 'message': "Запись добавлена"})
               

           elif request.POST.get('save_to') == 'file':
                # Преобразуем данные в формат XML и дополняем существующий файл
                added = create_or_update_xml_file(form.cleaned_data)
                if added:
                        return render(request, 'student_form.html', {'form': form, 'success': True, 'message': "Запись добавлена"})
                else:
                        return render(request, 'student_form.html', {'form': form, 'success': False, 'message': "Дублирующая запись"})

    return render(request, 'student_form.html', {'form': form})

def display_xml_data(request):
    xml_file_path = 'XMLfiles/performance.xml'  # Путь к XML-файлу
    data = []
    errors = []  # Список для хранения ошибок

    if os.path.exists(xml_file_path) and os.path.getsize(xml_file_path) > 0:
        try:
            # Разбор XML-файла
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Проход по элементам и добавление их в список
            for entry in root.findall('entry'):
                field_errors = []  # Для ошибок внутри одной записи

                # Получаем данные полей или указываем None, если данные отсутствуют
                name = entry.find('name').text if entry.find('name') is not None else None
                subject = entry.find('subject').text if entry.find('subject') is not None else None
                grade = entry.find('grade').text if entry.find('grade') is not None else None

                # Проверяем, какие данные отсутствуют, и добавляем сообщения об ошибке
                if name is None:
                    field_errors.append("Отсутствует имя.")
                if subject is None:
                    field_errors.append("Отсутствует предмет.")
                if grade is None:
                    field_errors.append("Отсутствует оценка.")

                # Если есть ошибки в записи, добавляем их в общий список ошибок
                if field_errors:
                    errors.append(f"Ошибка в записи с name={name or 'None'}: " + "; ".join(field_errors))

                # Добавляем запись в таблицу, даже если в ней есть ошибки
                data.append({
                    'name': name,
                    'subject': subject,
                    'grade': grade,
                })

        except ET.ParseError:
            errors.append("XML-файл повреждён и не может быть разобран.")  # Ошибка при парсинге файла
    else:
        errors.append("XML-файл не найден или пуст.")

    return render(request, 'display_xml_data.html', {'data': data, 'errors': errors})

# Объединённая функция для скачивания и загрузки XML файла

def manage_xml(request):
    errors = []  # Список для хранения сообщений об ошибках
    success_message = None  # Сообщение об успешном выполнении
    file_path = "XMLfiles/performance.xml"  # Путь к XML файлу

    # Регулярное выражение для проверки формата оценки
    grade_regex = re.compile(r'^[2-5]$')  # Регулярное выражение для проверки оценки (целое число)

    # Обрабатываем запрос на скачивание файла
    # Проверяем, был ли запрос на скачивание файла через GET-запрос
    if request.method == 'GET' and 'download' in request.GET:
        # Проверяем, существует ли файл performance.xml
        if os.path.exists(file_path):
            # Если файл существует, открываем его для чтения в двоичном режиме
            with open(file_path, 'rb') as xml_file:
                # Создаем ответ, возвращая содержимое файла как HTTP-ответ
                response = HttpResponse(xml_file.read(), content_type='application/xml')
                # Устанавливаем заголовок для скачивания файла (Content-Disposition)
                response['Content-Disposition'] = 'attachment; filename="performance.xml"'
                # Возвращаем ответ для скачивания файла
                return response

        else:
            errors.append("XML-файл не найден для скачивания.")

    # Обрабатываем запрос на загрузку файла
    if request.method == 'POST' and 'upload' in request.FILES:
        uploaded_file = request.FILES['upload']  # Получаем загруженный файл

        try:
            tree = ET.parse(uploaded_file)  # Пробуем разобрать XML файл
            root = tree.getroot()

            # Проверяем, что корневой элемент правильный (должен быть <data>)
            if root.tag != 'data':
                errors.append("Неверный формат XML файла. Ожидается корневой элемент <data>.")
            else:
                # Загружаем существующий XML файл, если он существует
                if os.path.exists(file_path):
                    existing_tree = ET.parse(file_path)
                    existing_root = existing_tree.getroot()
                else:
                    existing_root = ET.Element("data")
                    existing_tree = ET.ElementTree(existing_root)

                keys = ['name', 'subject', 'grade']
                records_added = 0  # Счётчик добавленных записей

                for entry in root.findall('entry'):
                    new_entry_data = {key: entry.find(key).text if entry.find(key) is not None else None for key in keys}

                    # Проверяем, что все ключи присутствуют в новой записи
                    if any(new_entry_data[key] is None for key in keys):
                        errors.append(f"Неполные данные в записи: {new_entry_data}")
                        continue  # Пропускаем неполные записи

                    # Список для хранения ошибок для текущей записи
                    entry_errors = []

                    # Проверка оценки (должна быть целым числом)
                    if not grade_regex.match(new_entry_data['grade']):
                        entry_errors.append(f"Ошибка: некорректная оценка.")

                    # Если есть ошибки для текущей записи, добавляем их в общий список ошибок
                    if entry_errors:
                        # Добавляем запись с ошибками в общий список ошибок
                        errors.append(f"Запись с ошибками: {new_entry_data}.{', '.join(entry_errors)}")
                        continue  # Пропускаем запись с ошибками

                    # Проверяем, нет ли такой записи уже в существующем файле
                    is_duplicate = any(
                        all(existing_entry.find(key).text == new_entry_data[key] for key in keys)
                        for existing_entry in existing_root.findall('entry')
                    )

                    # Если запись уникальна, добавляем её
                    if not is_duplicate:
                        new_entry = ET.SubElement(existing_root, "entry")
                        for key, value in new_entry_data.items():
                            child = ET.SubElement(new_entry, key)
                            child.text = value
                        records_added += 1  # Увеличиваем счетчик добавленных записей
                    else:
                        # Если запись является дубликатом, добавляем информацию об этом в список ошибок
                        errors.append(f"Дублирующая запись: {new_entry_data}")

                # Если хотя бы одна запись была добавлена, сохраняем файл с форматированием
                if records_added > 0:
                    # Добавляем отступы для форматирования
                    ET.indent(existing_tree, space="  ", level=0)
                    existing_tree.write(file_path, encoding="utf-8", xml_declaration=True)
                    success_message = f"Добавлено {records_added} новых записей в XML файл."
                else:
                    success_message = "Новые записи не были добавлены, так как все записи были дубликатами или содержали ошибки."

        except ET.ParseError:
            errors.append("Ошибка парсинга XML файла. Файл поврежден или не является корректным XML.")

    return render(request, 'upload_download_xml.html', {'errors': errors, 'success_message': success_message})


def display_db_data(request):
    # Извлекаем все данные из БД
    entries = Student.objects.all()

    # Передаем данные в шаблон
    return render(request, 'display_db_data.html', {'entries': entries})

    
# Функция для удаления записи из базы данных
def delete_entry(request, id):
    # Получаем объект записи из базы данных по его идентификатору (id).
    # Если запись не найдена, вызывается ошибка 404.
    entry = get_object_or_404(Student, id=id)
    
    # Проверяем, если запрос был отправлен методом POST.
    # Это обычно означает, что пользователь подтвердил удаление записи.
    if request.method == 'POST':
        # Удаляем запись из базы данных.
        entry.delete()
        # После удаления перенаправляем пользователя на страницу с отображением данных из базы.
        return redirect('display_db_data')
    
    # Если запрос был GET (то есть страница загрузилась без подтверждения удаления),
    # рендерим шаблон с подтверждением удаления.
    return render(request)

# Функция для редактирования записи в базе данных
def edit_entry(request, id):
    # Получаем объект записи по идентификатору (id) из базы данных.
    # Если запись не найдена, вызывается ошибка 404.
    entry = get_object_or_404(Student, id=id)
    
    # Если запрос был отправлен методом POST (это означает, что пользователь отправил форму с новыми данными),
    if request.method == 'POST':
        # Создаем форму, заполняя её данными, которые пришли с формы (request.POST),
        # а также передаем текущую запись (instance=entry), чтобы редактировать существующую запись, а не создавать новую.
        form = Student_form(request.POST, instance=entry)
        
        # Проверяем, корректна ли форма (валидна ли).
        if form.is_valid():
            # Если форма валидна, сохраняем изменения в базу данных.
            form.save()
            # После успешного редактирования перенаправляем пользователя на страницу с данными из базы.
            return redirect('display_db_data')
    else:
        # Если запрос был методом GET (то есть пользователь только открыл страницу для редактирования),
        # создаем форму, предварительно заполнив её данными из существующей записи (instance=entry).
        form = Student_form(instance=entry)
    
    # Рендерим страницу для редактирования записи и передаем туда форму, а также объект записи.
    return render(request, 'edit_entry.html', {'form': form, 'entry': entry})


def search_entries(request):
    # Получаем значение параметра 'query' из GET-запроса
    # Если параметр отсутствует, присваиваем ему пустую строку
    query = request.GET.get('query', '')
    
    # Фильтруем записи модели ExampleModel по трем полям:
    # - name, subject и grade, используя __icontains, который ищет подстроку
    # (регистронезависимый поиск)
    results = Student.objects.filter(
        name__icontains=query
    ) | Student.objects.filter(
        subject__icontains=query
    ) | Student.objects.filter(
        grade__icontains=query
    )

    # Преобразуем каждую запись в словарь, чтобы передать их в JSON-ответ
    entries = [{
        'id': entry.id,
        'name': entry.name,
        'subject': entry.subject,
        'grade': entry.grade,
    } for entry in results]

    # Возвращаем данные в формате JSON, чтобы они были обработаны JavaScript на клиенте
    return JsonResponse({'entries': entries})