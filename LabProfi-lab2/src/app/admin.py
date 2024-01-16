from django.contrib import admin
from .models import ServiceRequest, Specialist


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


admin.site.register(Specialist, SpecialistAdmin)
admin.site.register(ServiceRequest, ServiceRequestAdmin)
