import os
import shutil

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from filebrowser.models import Directory


FAKE_FB_ROOT = os.path.join(settings.BASE_DIR, 'filebrowser/tests/tmp')

RES_DIR = os.path.join(settings.BASE_DIR, "filebrowser/tests/ressources/fake_filebrowser_data/")



@override_settings(FILEBROWSER_ROOT=FAKE_FB_ROOT)
class LoadPLTPTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        if os.path.isdir(FAKE_FB_ROOT):
            shutil.rmtree(FAKE_FB_ROOT)
        
        cls.user = User.objects.create_user(username='user', password='12345', id=100)
        cls.c = Client()
        cls.c.force_login(cls.user, backend=settings.AUTHENTICATION_BACKENDS[0])
        cls.dir = Directory.objects.create(name='Yggdrasil', owner=cls.user)
        cls.lib = Directory.objects.create(name='lib', owner=cls.user)
        
        shutil.rmtree(os.path.join(cls.dir.root))
        shutil.copytree(RES_DIR, cls.dir.root)
    
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(FAKE_FB_ROOT)
        super().tearDownClass()
    
    
    def test_load_pltp(self):
        response = self.c.get(reverse("filebrowser:option"), {
                'name': 'load_pltp',
                'path': 'Yggdrasil/working.pltp',
        }, content_type='application/json')
        self.assertContains(response, "http://testserver/playexo/activity/1/", status_code=200)
    
    
    def test_load_pltp_no_path(self):
        response = self.c.get(reverse("filebrowser:option"), {
                'name': 'load_pltp',
        }, content_type='application/json')
        self.assertContains(response, '"path" parameter is missing', status_code=400)
    
    
    def test_reload_pltp(self):
        response = self.c.get(reverse("filebrowser:option"), {
                'name': 'load_pltp',
                'path': 'Yggdrasil/working.pltp',
        }, content_type='application/json')
        self.assertContains(response, "http://testserver/playexo/activity/1/", status_code=200)
        response = self.c.post(reverse("filebrowser:option"), {
                'name'       : 'reload_pltp',
                'path'       : 'Yggdrasil/working.pltp',
                'activity_id': 1,
        }, content_type='application/json')
        self.assertContains(response, "recharg", status_code=200)
    
    
    def test_reload_no_path(self):
        response = self.c.post(reverse("filebrowser:option"), {
                'name'       : 'reload_pltp',
                'activity_id': 1,
        }, content_type='application/json')
        self.assertContains(response, "parameter 'path' is missing", status_code=400)
    
    
    def test_reload_no_activity_id(self):
        response = self.c.post(reverse("filebrowser:option"), {
                'name': 'reload_pltp',
                'path': 'Yggdrasil/working.pltp',
        }, content_type='application/json')
        self.assertContains(response, "Missing 'activity_id' parameter", status_code=400)
    
    
    def test_test_pl(self):
        response = self.c.get(reverse("filebrowser:option"), {
                'name': 'test_pl',
                'path': 'Yggdrasil/working.pl',
        }, content_type='application/json')
        self.assertContains(response, "UPEM - PL", status_code=200)
    

    def test_test_pl_no_path(self):
        response = self.c.get(reverse("filebrowser:option"), {
                'name': 'test_pl',
        }, content_type='application/json')
        self.assertContains(response, '"path" parameter is missing', status_code=400)
        
        
    def test_test_pl_unknown_path(self):
        response = self.c.get(reverse("filebrowser:option"), {
                'name': 'test_pl',
                'path': 'Yggdrasil/unknown.pl',
        }, content_type='application/json')
        self.assertContains(response, 'No such file or directory:', status_code=400)
