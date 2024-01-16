from datetime import datetime

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.contrib.auth.models import User, UserManager, PermissionsMixin
from django.contrib.auth.models import AbstractUser

from specialistsProject import settings


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True, verbose_name="Логин")
    full_name = models.CharField(max_length=150, verbose_name="ФИО")
    email = models.EmailField(("email"), unique=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон", null=True, blank=True)
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь модератором?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")

    USERNAME_FIELD = 'username'
    objects = UserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


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
    specialist = models.ManyToManyField(Specialist, related_name="requests", verbose_name="Специалисты",
                                        through="ServiceRequestSpecialist")
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="creator", verbose_name="Создатель")
    moderator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="moderator", verbose_name="Модератор", null=True, blank=True)
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
