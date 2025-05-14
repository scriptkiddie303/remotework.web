from django.contrib import admin
from firstapp.models import Service
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'price', 'created_at', 'updated_at')
    search_fields = ('title',)
    list_filter = ('created_at',)
admin.site.register(Service, ServiceAdmin)
# Register your models here.
