from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, RegexValidator
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from .models import Category, Request, Status


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name in ('username', 'password'):
            field = self.fields[name]
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


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
        validators=[name_validator],
        required=False,
        empty_value=None,
    )

    accept_terms = forms.BooleanField(
        label='Согласие на обработку персональных данных',
        label_suffix='',
        required=True,
    )

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('username', 'email', 'first_name', 'last_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Повторите пароль'
        self.fields['username'].label = 'Логин'

        self.fields['username'].help_text='Только латинские буквы и дефис.'

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


class RequestCreateForm(BootstrapFormMixin, forms.ModelForm):
    title = forms.CharField(max_length=150, label="Название", required=True)
    description = forms.CharField(max_length=255, label='Описание', required=True)
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label='Категория',
        required=True,
        empty_label='Выберите категорию'
    )
    plan_image = forms.ImageField(
        label='План помещения',
        required=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=('jpg', 'jpeg', 'png', 'bmp'),
                message='Загрузите файл с расширением JPG, JPEG, PNG или BMP.',
            ),
        ],
    )

    class Meta:
        model = Request
        fields = ('title', 'description', 'category', 'plan_image')

    def clean_plan_image(self):
        upload = self.cleaned_data['plan_image']
        if upload.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Размер файла не должен превышать 2 МБ.')
        if upload.image.format not in {'JPEG', 'PNG', 'BMP'}:
            raise forms.ValidationError('Загрузите изображение в формате JPEG, PNG или BMP.')

        return upload


class RequestUpdateForm(RequestCreateForm):
    def clean_plan_image(self):
        if 'plan_image' in self.changed_data:
            return super().clean_plan_image()
        return self.cleaned_data['plan_image']


class RequestStatusForm(BootstrapFormMixin, forms.Form):
    status = forms.ModelChoiceField(
        queryset=Status.objects.filter(code__in=(Status.Code.IN_PROGRESS, Status.Code.COMPLETED)),
        label='Статус',
        empty_label='Выберите статус',
    )
    comment = forms.CharField(label='Комментарий', widget=forms.Textarea, required=False)
    final_image = forms.ImageField(label='Готовый дизайн', required=False)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        if status is None:
            return cleaned_data

        if status.code == Status.Code.IN_PROGRESS and not cleaned_data.get('comment'):
            self.add_error('comment', 'Добавьте комментарий, чтобы принять заявку в работу.')
        elif (
            status.code == Status.Code.COMPLETED
            and 'final_image' in cleaned_data
            and cleaned_data['final_image'] is None
        ):
            self.add_error('final_image', 'Загрузите готовый дизайн, чтобы завершить заявку.')

        return cleaned_data


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name',)
        labels = {'name': 'Название'}
        help_texts = {'name': ''}


class StyledPasswordResetForm(BootstrapFormMixin, PasswordResetForm):
    pass


class StyledSetPasswordForm(BootstrapFormMixin, SetPasswordForm):
    pass
