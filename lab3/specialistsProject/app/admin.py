from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import ServiceRequest, Specialist, ServiceRequestSpecialist


class SpecialistInline(admin.TabularInline):
    model = ServiceRequest.specialist.through
    extra = 0
    verbose_name = "специалист связанный с заявкой"
    verbose_name_plural = "Специалисты связанные с заявкой"


class ServiceRequestInline(admin.TabularInline):
    model = ServiceRequest.specialist.through
    extra = 0
    verbose_name = "заявка"
    verbose_name_plural = "Заявки связанные с специалистом"


class ServiceRequestAdmin(admin.ModelAdmin):
    inlines = [SpecialistInline]
    exclude = ["specialist"]


class SpecialistAdmin(admin.ModelAdmin):
    inlines = [ServiceRequestInline]


class ServiceRequestSpecialistAdmin(admin.ModelAdmin):
    list_display = ['specialist', 'service_request']


admin.site.register(Specialist, SpecialistAdmin)
admin.site.register(ServiceRequest, ServiceRequestAdmin)
admin.site.register(ServiceRequestSpecialist, ServiceRequestSpecialistAdmin)
