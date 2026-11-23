from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)


class BootstrapFormMixin:
    """Adds Bootstrap 5 classes to every visible widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css = 'form-check-input' if isinstance(widget, forms.CheckboxInput) else 'form-control'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {css}".strip()
            widget.attrs.setdefault('placeholder', field.label)

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            if name in self.fields:
                attrs = self.fields[name].widget.attrs
                attrs['class'] = f"{attrs.get('class', '')} is-invalid".strip()


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    username = forms.CharField(label='Логин')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

name_validator = RegexValidator(
    regex=r'^[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)*\Z',
    message='Допускаются только русские буквы и дефис.',
)

username_validator = RegexValidator(regex=r'^[A-Za-z-]+\Z')

class RegistrationForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(label='Email')

    first_name = forms.CharField(
        max_length=150,
        label='Имя',
        validators=[name_validator],
        required=True,
    )

    last_name = forms.CharField(
        max_length=150,
        label='Фамилия',
        validators=[name_validator],
        required=True,
    )

    patronymic = forms.CharField(
        max_length=150,
        label='Отчество',
        validators=[name_validator], required=False,
    )

    accept_terms = forms.BooleanField(
        label='Согласие на обработку персональных данных',
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повторите пароль'
        self.fields['username'].label = 'Логин'

        self.fields['username'].validators=[username_validator]

        for name in ('username', 'password1', 'password2'):
            field = self.fields[name]
            field.widget.attrs['placeholder'] = field.label

    def clean_email(self):
        email = self.cleaned_data['email'].lower()

        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Пользователь с таким email уже существует.'
            )

        return email

class StyledPasswordResetForm(BootstrapFormMixin, PasswordResetForm):
    pass


class StyledSetPasswordForm(BootstrapFormMixin, SetPasswordForm):
    pass
