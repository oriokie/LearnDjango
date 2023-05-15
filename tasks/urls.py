from django.urls import path
from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.index, name="index"),
    path("add", views.add, name="add"),
    path("read", views.read, name="read"),
    path("stat", views.stat, name="stat"),
    path("donate", views.donate, name="donate"),
    path("donors_list", views.donors_list, name="donors_list"),
]
