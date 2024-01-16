from django.contrib.auth.hashers import make_password

from .forms import UserRegistrationForm
from auth_users.models import User


def create_user(request):
    user_form = UserRegistrationForm(request.POST)
    if user_form.is_valid():
        # Create a new user object but avoid saving it yet
        new_user = user_form.save(commit=False)
        # Set the chosen password
        new_user.set_password(user_form.cleaned_data['password'])
        # Save the User object
        new_user.save()
        return new_user


def update_user(user: User, first_name, last_name, email):
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.save()


def change_password(user: User, new_password):
    user.set_password(new_password)
    user.save()