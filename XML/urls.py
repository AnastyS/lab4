"""
URL configuration for XML project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.student_form, name='student_form'),
    path('display/', views.display_xml_data, name='display_xml_data'),
    path('manage_xml/', views.manage_xml, name='manage_xml'),

    path('display_db/', views.display_db_data, name='display_db_data'),
    path('edit/<int:id>/', views.edit_entry, name='edit_entry'),
    path('delete_entry/<int:id>/', views.delete_entry, name='delete_entry'),
    path('search/', views.search_entries, name='search_entries'),
]
