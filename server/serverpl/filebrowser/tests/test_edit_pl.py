import shutil
from os.path import join, isdir

from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.contrib.auth.models import User

from filebrowser.models import Directory


FAKE_FB_ROOT = join(settings.BASE_DIR, 'filebrowser/tests/ressources')
VALUE = "text==\n# Fonctions\n\nEcrire une fonction **bob** qui retourne la valeur"

@override_settings(FILEBROWSER_ROOT=FAKE_FB_ROOT)
class EditPLTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='user', password='12345', id=100)
        cls.c = Client()
        cls.c.force_login(cls.user, backend=settings.AUTHENTICATION_BACKENDS[0])
        rel = join(settings.FILEBROWSER_ROOT, '100/')
        if isdir(rel):
            shutil.rmtree(join(rel))
        cls.folder = Directory.objects.get(name='100', owner=cls.user)
        shutil.copytree(join(FAKE_FB_ROOT, 'fake_filebrowser_data'), cls.folder.root)
        
    
    def test_method_not_allowed(self):
        response = self.c.post(
            '/filebrowser/home/TPE/opt/',
            {
                'option': 'entry-direct-edit_pl',
                'target': '.',
                   
            },
            follow=True
        )
        self.assertEqual(response.status_code, 405)
    
    def test_editpl_file(self):
        try:
            response = self.c.get(
                '/filebrowser/home/TPE/opt/?option=entry-direct-edit_pl&target=function001.pl',
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, VALUE)
        except AssertionError:
            m = list(response.context['messages'])
            if m:
                print("\nFound messages:")
                [print(i.level, ': ', i.message)for i in m]
            raise

    def test_editpl_file_not_pl(self):
        try:
            response = self.c.get(
                '/filebrowser/home/opt/?option=entry-direct-edit_pl&target=truc.pl',
                follow=True
            )
            
            self.assertEqual(response.status_code, 200)
        except AssertionError:
            m = list(response.context['messages'])
            if m:
                print("\nFound messages:")
                [print(i.level, ': ', i.message)for i in m]
            raise
