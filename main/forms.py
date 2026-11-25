from unicodedata import name as unicode_name

from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator, RegexValidator
from django.contrib.auth.forms import (
    AuthenticationForm,
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
    username = forms.CharField(
        strip=False,
        widget=forms.TextInput(attrs={'autocomplete': 'username', 'autofocus': True}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, label in (('username', 'Логин'), ('password', 'Пароль')):
            field = self.fields[name]
            field.label = label
            field.widget.attrs['placeholder'] = label


def validate_name(value):
    letters = value.replace(' ', '').replace('-', '')
    if not letters or any(
        not letter.isalpha() or not unicode_name(letter, '').startswith('CYRILLIC ')
        for letter in letters
    ):
        raise forms.ValidationError('Допускаются только кириллические буквы, пробелы и дефисы.')


class RegistrationForm(BootstrapFormMixin, UserCreationForm):
    username = forms.CharField(
        label='Логин',
        max_length=get_user_model()._meta.get_field('username').max_length,
        strip=False,
        help_text='Только латинские буквы и дефис.',
        validators=[RegexValidator(r'\A[A-Za-z-]+\Z', 'Допускаются только латинские буквы и дефис.')],
        widget=forms.TextInput(attrs={'autocomplete': 'username'}),
    )
    email = forms.EmailField(label='Email')

    first_name = forms.CharField(
        max_length=150,
        label='Имя',
        validators=[validate_name],
        required=True,
    )

    last_name = forms.CharField(
        max_length=150,
        label='Фамилия',
        validators=[validate_name],
        required=True,
    )

    patronymic = forms.CharField(
        max_length=150,
        label='Отчество',
        validators=[validate_name],
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
        for name in ('password1', 'password2'):
            field = self.fields[name]
            field.widget.attrs['placeholder'] = field.label

    def clean_email(self):
        return self.cleaned_data['email'].lower()


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
        widget=forms.FileInput,
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
