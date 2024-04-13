from django.urls import path
from . import views

app_name='user_session'
urlpatterns = [
    path('',views.login,name='login'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('past_interviews/',views.past_interviews,name='past_interviews'),
    path('register/',views.register,name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('start_analysis_view/', views.start_analysis_view, name='start_analysis_view'),
    path('check_analysis_result/', views.check_analysis_result, name='check_analysis_result'),
    path('check_login_status/', views.check_login_status, name='check_login_status'),
    path('clear_analysis_results/', views.clear_analysis_results, name='clear_analysis_results'),
    path('resultpie/', views.result_pie_view, name='result_pie'),
]


