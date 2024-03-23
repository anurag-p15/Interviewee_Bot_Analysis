from django.urls import path
from . import views

app_name='user_session'
urlpatterns = [
    path('',views.login,name='login'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('past_interviews/',views.past_interviews,name='past_interviews'),
    path('register/',views.register,name='register'),
]
