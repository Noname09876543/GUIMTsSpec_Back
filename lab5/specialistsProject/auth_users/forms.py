from django.contrib.auth.models import User
from django import forms
from django.core.files.images import get_image_dimensions



class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Пароль(повторно)', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'username': 'Имя пользователя',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }
        help_texts = {
            'username': '',
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']


class ProfileForm(forms.Form):
    first_name = forms.CharField(
        label="Имя:",
        widget=forms.TextInput,
    )
    last_name = forms.CharField(
        label="Фамилия:",
        widget=forms.TextInput,
    )
    email = forms.EmailField(
        label="email:",
        widget=forms.TextInput,
    )


class ChangePasswordForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    old_password = forms.CharField(
        label="Старый пароль:",
        widget=forms.PasswordInput,
    )
    new_password = forms.CharField(
        label="Новый пароль:",
        widget=forms.PasswordInput,
    )
    new_password_repeat = forms.CharField(
        label="Новый пароль(повторно):",
        widget=forms.PasswordInput,
    )

    def clean_old_password(self):
        password = self.cleaned_data['old_password']
        if not self.user.check_password(password):
            self.add_error('old_password', forms.ValidationError('Пароль указан неверно'))
        return password

    def clean_new_password_repeat(self):
        password1 = self.cleaned_data['new_password']
        password2 = self.cleaned_data['new_password_repeat']
        if password1 != password2:
            self.add_error('new_password_repeat', forms.ValidationError('Пароли не совпадают'))
        return password1

