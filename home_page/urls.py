from django.urls import path
from . import views

app_name='home_page'
urlpatterns = [
    path('',views.home,name='home'),
    path('domain/',views.domain,name='domain'),
]
