"""
URL configuration for watcher project.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('monitor.urls')),
    path('dashboard/', include('monitor.frontend_urls')),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
]
