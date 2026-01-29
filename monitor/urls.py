from django.urls import path
from . import views

app_name = 'monitor'

urlpatterns = [
    path('applications/', views.ApplicationListCreate.as_view(), name='application-list'),
    path('applications/<int:pk>/', views.ApplicationDetail.as_view(), name='application-detail'),
    path('applications/<int:pk>/history/', views.ApplicationHistory.as_view(), name='application-history'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
]
