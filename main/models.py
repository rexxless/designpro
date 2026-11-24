from django.conf import settings
from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.db.models.functions import Lower
from django.urls import reverse

# Create your models here.

class Request(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    category = models.ForeignKey('Category', on_delete=models.RESTRICT)
    plan_image = models.ImageField(upload_to='requests')
    final_image = models.ImageField(upload_to='requests', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.ForeignKey('Status', on_delete=models.RESTRICT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        """String for representing the Model object."""
        return f"{self.title} - {self.status}"

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this book."""
        return reverse('request-detail', args=[str(self.id)])


class Category(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Enter the category name.",
    )

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a particular genre instance."""
        return reverse('category-detail', args=[str(self.id)])

    class Meta:
        ordering = ['name']
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='category_name_case_insensitive_unique',
                violation_error_message="Category already exists (case-insensitive match)"
            ),
        ]

class Status(models.Model):
    class Code(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'Принято в работу'
        COMPLETED = 'completed', 'Выполнено'

    code = models.CharField(max_length=16, choices=Code.choices, unique=True, null=True, blank=True)
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Enter the status name."
    )

    def __str__(self):
        """String for representing the Model object."""
        return self.name

    def get_absolute_url(self):
        """Returns the url to access a particular status instance."""
        return reverse('status-detail', args=[str(self.id)])

    class Meta:
        ordering = ['name']
        constraints = [
            UniqueConstraint(
                Lower('name'),
                name='status_name_case_insensitive_unique',
                violation_error_message="Status already exists (case-insensitive match)"
            ),
        ]


class Profile(models.Model):
    patronymic = models.CharField(null=True, max_length=150)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        """String for representing the Model object."""
        return self.user.username

    def get_full_name(self):
        """String for displaying user's full name."""
        name = [self.user.last_name, self.user.first_name]
        if self.patronymic:
            name.append(self.patronymic)
        return str(' '.join(name))



