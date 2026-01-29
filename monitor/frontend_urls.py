from django.urls import path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

urlpatterns = [
    path('', ensure_csrf_cookie(TemplateView.as_view(template_name='dashboard/index.html')), name='dashboard-index'),
]
