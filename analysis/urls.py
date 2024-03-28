from django.urls import path
from . import views

app_name= 'analysis'

urlpatterns = [
    path('',views.start_interview ,name='start_interview'),
   
]

