from django.contrib import admin
from .models import WatchedApplication, CheckResult


@admin.register(WatchedApplication)
class WatchedApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'base_url', 'hostname', 'check_interval_seconds',
        'is_active', 'client_p12_path', 'updated_at',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'base_url', 'hostname')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = ('watched_application', 'checked_at', 'status_code', 'response_time_ms', 'success')
    list_filter = ('success', 'watched_application')
    readonly_fields = (
        'watched_application', 'checked_at', 'status_code',
        'response_time_ms', 'success', 'error_message',
    )
    date_hierarchy = 'checked_at'
