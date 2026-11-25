from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models, router, transaction
from django.db.models.constraints import UniqueConstraint
from django.db.models.functions import Collate, Lower
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse

# Create your models here.

class Request(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    plan_image = models.ImageField(upload_to='requests')
    final_image = models.ImageField(upload_to='requests', blank=True, null=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.ForeignKey('Status', on_delete=models.RESTRICT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']

    def save(self, *, using=None, update_fields=None, **kwargs):
        database = using or router.db_for_write(type(self), instance=self)
        image_fields = ('plan_image', 'final_image')
        if update_fields is not None:
            update_fields = frozenset(update_fields)
            image_fields = [field for field in image_fields if field in update_fields]
        if self.pk is None or not image_fields:
            return super().save(using=database, update_fields=update_fields, **kwargs)

        with transaction.atomic(using=database):
            old_images = (
                Request.objects.using(database).select_for_update()
                .filter(pk=self.pk).values_list(*image_fields).first()
            )
            super().save(using=database, update_fields=update_fields, **kwargs)
            if old_images:
                replaced = {
                    old for field, old in zip(image_fields, old_images)
                    if old and old != getattr(self, field).name
                }
                delete_unused_images_after_commit(replaced, database)

    def __str__(self):
        """String for representing the Model object."""
        return f"{self.title} - {self.status}"

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this book."""
        return reverse('request-detail', args=[str(self.id)])


def delete_unused_images_after_commit(names, database):
    def delete_unused_images():
        requests = Request.objects.using(database)
        for name in names:
            if not requests.filter(models.Q(plan_image=name) | models.Q(final_image=name)).exists():
                default_storage.delete(name)

    if names:
        transaction.on_commit(delete_unused_images, using=database, robust=True)


@receiver(pre_delete, sender=Request)
def clean_deleted_request_images(sender, instance, using, **kwargs):
    images = (sender.objects.using(using).filter(pk=instance.pk)
              .values_list('plan_image', 'final_image').first())
    if images:
        delete_unused_images_after_commit({name for name in images if name}, using)


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
        return reverse('category-detail', args=[self.pk])

    class Meta:
        ordering = ['name']
        constraints = [
            UniqueConstraint(
                Collate('name', 'portal_casefold'),
                name='category_name_case_insensitive_unique',
                violation_error_message='Категория с таким названием уже существует.'
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



