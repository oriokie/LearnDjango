from django.urls import path
from .views import upload_file, file_list

urlpatterns = [
    path('upload/', upload_file, name='upload_file'),
    path('files/', file_list, name='file_list')
]
