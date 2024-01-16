from django.urls import path
from . import views
from .views import profile_edit

urlpatterns = [
    path('profile/', views.profile, name="profile"),
    path('profile/edit', profile_edit, name="edit_profile"),
    path('signup/', views.register, name="signup"),
]