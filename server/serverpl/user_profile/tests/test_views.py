from django.test import TestCase, Client
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.messages import constants as messages

from user_profile.enums import ColorBlindness, EditorTheme


class ViewsTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='12345')
        cls.c = Client()
        cls.c.force_login(cls.user, backend=settings.AUTHENTICATION_BACKENDS[0])


    def test_views_edit_profile(self):
        response = self.c.post(
            '/profile/', {
                 "color_blindness": ColorBlindness.PROTANOPIA,
                 'editor_theme': EditorTheme.GOB,
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.user = User.objects.get(pk=self.user.pk)

        self.assertEqual(self.user.profile.color_blindness, ColorBlindness.PROTANOPIA)
        self.assertEqual(self.user.profile.editor_theme, EditorTheme.GOB)

        m = list(response.context['messages'])
        self.assertEqual(len(m), 1)
        self.assertEqual(m[0].level, messages.INFO)

        self.assertTemplateUsed(response, 'user_profile/edit_profile.html')
        self.assertContains(response, "Paramètres")


    def test_views_editor_preview(self):
        response = self.c.post(
            '/profile/editor_preview/',
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prévisualisation des colorisation syntaxique de l'éditeur "
                                      "de texte")
