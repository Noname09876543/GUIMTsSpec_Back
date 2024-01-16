from datetime import datetime
from django.db import models
from django.contrib.auth.models import User


class Specialist(models.Model):
    name = models.CharField(max_length=40, unique=True, verbose_name="Имя")
    desc = models.TextField(null=True, blank=True, verbose_name="Описание")
    preview_image = models.ImageField(upload_to="specialist_preview_img", blank=True, null=True,
                                      verbose_name="Изображение")
    # preview_image = models.BinaryField(editable=True, blank=True, null=True, verbose_name="Изображение")

    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "Специалист"
        verbose_name_plural = "Специалисты"

    def __str__(self):
        return f'''Специалист "{self.name}" ({'Активен' if self.is_active else 'Не активен'})'''


class ServiceRequest(models.Model):
    specialist = models.ManyToManyField(Specialist, related_name="requests", verbose_name="Специалисты", through="ServiceRequestSpecialist")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="creator", verbose_name="Создатель")
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="moderator", verbose_name="Модератор")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    STATUS_CHOICES = [
        ("CREATED", "Создана"),
        ("IN_WORK", "В работе"),
        ("CANCELED", "Отменена"),
        ("FINISHED", "Завершена"),
        ("DELETED", "Удалена"),
    ]
    status = models.CharField(
        max_length=8,
        choices=STATUS_CHOICES,
        default="CREATED",
        verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    formed_at = models.DateTimeField(blank=True, null=True, verbose_name="Сформировано")
    finished_at = models.DateTimeField(blank=True, null=True, verbose_name="Завершено")

    class Meta:
        verbose_name = "заявка"
        verbose_name_plural = "Заявки"

    def __str__(self):
        created_date_time = datetime.fromtimestamp(self.created_at.timestamp())
        return f'''Заявка {created_date_time.strftime("%H:%M:%S %d.%m.%Y")} от {self.creator.username} ({self.get_status_display()})'''


class ServiceRequestSpecialist(models.Model):
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, verbose_name="Специалист")
    service_request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, verbose_name="Заявка")

    def __str__(self):
        return f'{self.specialist} {self.service_request}'

    class Meta:
        verbose_name = "Связь специалист - заявка"
        verbose_name_plural = "Связи специалист - заявка"