from django.urls import path
from . import views

app_name= 'analysis'

urlpatterns = [
    path('',views.start_interview ,name='start_interview'),
    path('start_analysis_view/', views.start_analysis_view, name='start_analysis_view'),
    path('check_analysis_result/', views.check_analysis_result, name='check_analysis_result'),
]

