from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Category, Request, Status


class PortalAccountTests(TestCase):
    def setUp(self):
        self.password = 'Portal-test-8374'
        self.registration = {
            'username': 'new-member',
            'email': 'admin@example.com',
            'first_name': 'Анна',
            'last_name': 'Орлова',
            'password1': self.password,
            'password2': self.password,
            'accept_terms': 'on',
        }

    def test_registration_accepts_shared_email_and_optional_patronymic(self):
        response = self.client.post(reverse('register'), self.registration)
        self.assertRedirects(response, reverse('request-list'))
        user = get_user_model().objects.get(username='new-member')
        self.assertEqual(user.email, get_user_model().objects.get(username='admin').email)
        self.assertIsNone(user.profile.patronymic)

    def test_registration_checks_characters_as_entered_and_duplicate_usernames(self):
        for username in ('ⓐlex', 'ａｌｅｘ', 'alex1', ' alex', 'al ex', 'ADMIN'):
            with self.subTest(username=username):
                response = self.client.post(reverse('register'), {**self.registration, 'username': username})
                self.assertIn('username', response.context['form'].errors)

    def test_member_login_opens_cabinet_and_exposes_account_actions(self):
        get_user_model().objects.create_user(username='alex', password=self.password)
        login_url = reverse('login')
        response = self.client.post(login_url, {'username': 'ⓐlex', 'password': self.password})
        self.assertTrue(response.context['form'].non_field_errors())
        response = self.client.post(login_url, {
            'username': 'alex', 'password': self.password, 'next': reverse('request-create'),
        }, follow=True)
        self.assertRedirects(response, reverse('request-list'))
        self.assertContains(response, reverse('password_change'))
        self.assertContains(response, 'Выход')
        self.assertNotContains(response, reverse('admin:index'))

    def test_seeded_admin_login_opens_studio_with_admin_navigation(self):
        response = self.client.post(reverse('login'), {
            'username': 'admin', 'password': 'admin', 'next': reverse('request-create'),
        }, follow=True)
        self.assertRedirects(response, reverse('studio-dashboard'))
        self.assertContains(response, reverse('admin:index'))
        self.assertContains(response, reverse('password_change'))


class StudioRequestTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.get(username='admin')
        self.member = get_user_model().objects.create_user('member')
        self.category = Category.objects.get(name='Эскиз')
        self.pending = Status.objects.get(code=Status.Code.NEW)

    def make_request(self, title, **fields):
        values = dict(user=self.member, category=self.category, status=self.pending,
                      description='Описание', plan_image='requests/plan.png')
        values.update(fields)
        return Request.objects.create(title=title, **values)

    def test_russian_category_duplicates_rejected_by_form_and_database(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse('studio-category-list'), {'name': 'эСКИЗ'})
        self.assertContains(response, 'Категория с таким названием уже существует.')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Category.objects.create(name='эскиз')

    def test_group_pages_show_only_matching_requests_to_administrators(self):
        other = Category.objects.get(name='2D-дизайн')
        completed = Status.objects.get(code=Status.Code.COMPLETED)
        both = self.make_request('Обе группы')
        category_only = self.make_request('Та же категория', user=self.admin, status=completed)
        status_only = self.make_request('Тот же статус', category=other, user=self.admin)
        staff = get_user_model().objects.create_user('staff', is_staff=True)
        for group, expected in ((self.category, [category_only, both]), (self.pending, [status_only, both])):
            url = group.get_absolute_url()
            self.client.logout()
            self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")
            for user in (self.member, staff):
                self.client.force_login(user)
                self.assertEqual(self.client.get(url).status_code, 403)
            self.client.force_login(self.admin)
            response = self.client.get(url)
            self.assertEqual(list(response.context['design_requests']), expected)
            self.assertContains(response, both.get_absolute_url())
        empty = Category.objects.create(name='Пустая категория')
        self.assertContains(self.client.get(empty.get_absolute_url()), 'Заявок пока нет.')
        self.assertContains(self.client.get(reverse('studio-dashboard')), self.pending.get_absolute_url())
        self.assertContains(self.client.get(reverse('studio-category-list')), self.category.get_absolute_url())

    def test_saved_comment_and_list_headings(self):
        item = self.make_request('Комната')
        self.client.force_login(self.admin)
        self.client.post(reverse('studio-request-status', args=[item.pk]), {
            'status': Status.objects.get(code=Status.Code.IN_PROGRESS).pk,
            'comment': 'Уточним размеры окна.',
        })
        self.assertContains(self.client.get(reverse('studio-dashboard')), 'Уточним размеры окна.')
        self.assertContains(self.client.get(reverse('request-list')), '<h1>Заявки</h1>', html=True)
        self.client.force_login(self.member)
        self.assertContains(self.client.get(item.get_absolute_url()), 'Уточним размеры окна.')
        self.assertContains(self.client.get(reverse('request-list')), '<h1>Мои заявки</h1>', html=True)

    def test_replacement_and_cascade_delete_only_unreferenced_files(self):
        with TemporaryDirectory() as directory, self.settings(MEDIA_ROOT=directory):
            old = default_storage.save('requests/old.png', ContentFile(b'plan'))
            shared = default_storage.save('requests/design.png', ContentFile(b'design'))
            item = self.make_request('Первая', plan_image=old, final_image=shared)
            other = self.make_request('Вторая', category=Category.objects.get(name='2D-дизайн'), plan_image=shared)
            with self.captureOnCommitCallbacks(execute=True):
                item.plan_image = ContentFile(b'replacement', name='replacement.png')
                item.save(update_fields=['plan_image'])
                self.assertTrue(default_storage.exists(old))
            self.assertFalse(default_storage.exists(old))
            with self.captureOnCommitCallbacks(execute=True):
                with transaction.atomic():
                    self.category.delete()
                    transaction.set_rollback(True)
            self.assertTrue(default_storage.exists(item.plan_image.name))
            with self.captureOnCommitCallbacks(execute=True):
                Category.objects.get(name='Эскиз').delete()
            self.assertFalse(default_storage.exists(item.plan_image.name))
            self.assertTrue(default_storage.exists(shared))
            with self.captureOnCommitCallbacks(execute=True):
                other.delete()
            self.assertFalse(default_storage.exists(shared))
