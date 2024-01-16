from django.db import models
from django.contrib.auth.models import User


# class Profile(models.Model):
#     avatar = models.ImageField(upload_to="avatars", blank=True, null=True)
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")