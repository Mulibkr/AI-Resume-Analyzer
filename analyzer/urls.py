from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('result/<int:report_id>/', views.result, name='result'),
    path('history/', views.history, name='history'),
    path('delete/<int:report_id>/', views.delete_report, name='delete_report'),
]
