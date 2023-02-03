from django.urls import path
from . import views

urlpatterns = [
    path("",views.index, name="index"),
    path("edwin",views.edwin, name="edwin"),
    path("david",views.david, name="david"),
    path("<str:name>",views.greet, name="greet")
]