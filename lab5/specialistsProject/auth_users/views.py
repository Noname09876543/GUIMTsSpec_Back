from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import UserRegistrationForm, ProfileForm, ChangePasswordForm
from .services import create_user, update_user, change_password


def register(request):
    if request.method == 'POST':
        new_user = create_user(request)
        return render(request, 'registration/register_done.html', {'new_user': new_user})
    else:
        if request.user.is_authenticated:
            return render(request, 'registration/register.html', {'ask_logout': True})
        user_form = UserRegistrationForm()
        return render(request, 'registration/register.html', {'user_form': user_form})


def profile(request):
    profile_form = ProfileForm(initial={
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email
    })
    if request.method == 'POST':
        password_form = ChangePasswordForm(request.POST, user=request.user)
        if password_form.is_valid():
            user = request.user
            change_password(request.user, password_form.cleaned_data['new_password'])
    else:
        password_form = ChangePasswordForm(user=request.user)
    page_data = {'profile_form': profile_form, 'password_form': password_form}
    return render(request, "registration/profile.html", page_data)


@require_http_methods(["POST"])
def profile_edit(request):
    form = ProfileForm(request.POST, request.FILES)
    if form.is_valid():
        update_user(
            request.user,
            form.cleaned_data['first_name'],
            form.cleaned_data['last_name'],
            form.cleaned_data['email']
        )
    return redirect(reverse('profile'))

