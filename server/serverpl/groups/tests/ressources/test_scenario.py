#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  test_parsers.py
#
#  Copyright 2018 Coumes Quentin <qcoumes@etud.u-pem.fr>
#

import shutil

from os.path import join, isdir, isfile

from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.messages import constants as messages
from django.forms.fields import DateTimeField

from groups.models import Groups, RequiredGroups
from playexo.models import Homework
from classmanagement.models import Course
from loader.models import PLDM

FAKE_FB_ROOT = join(settings.BASE_DIR, 'groups/tests/ressources')


@override_settings(FILEBROWSER_ROOT=FAKE_FB_ROOT)
class GroupsTestCase(TestCase):
    @classmethod

    def setUpTestData(self):
        self.user = User.objects.create_user(username='user', password='12345', id=100)
        self.c = Client()
        self.c.force_login(self.user, backend=settings.AUTHENTICATION_BACKENDS[0])


    def test_scenario(self):
        teacher = User.objects.create_user(username='teacher', password='12345', id=100)
        user1 = User.objects.create_user(username='user1', password='12345', id=100)
        user2 = User.objects.create_user(username='user2', password='12345', id=100)
        user3 = User.objects.create_user(username='user3', password='12345', id=100)
        user4 = User.objects.create_user(username='user4', password='12345', id=100)
        user5 = User.objects.create_user(username='user5', password='12345', id=100)
        user6 = User.objects.create_user(username='user6', password='12345', id=100)

        course = Course(name='Prog C', label="TEST")
        course.teacher.add(teacher)
        course.student.add(user1)
        course.student.add(user2)
        course.student.add(user3)
        course.student.add(user4)
        course.student.add(user5)
        course.student.add(user6)
        course.save()

        name = 'String in C'

        pldm = PLDM(
            sha1 = "test1234",
            name = name,
            rel_path = '/test_scenario_groups'
        )
        pldm.save()

        homework = Homework(
            pldm=pldm,
            open=1,
            name=name,
            date_deposit_end=DateTimeField().clean('2018-12-10 23:55'),
            deposit_number=1,
            deposit_size=10,
            id_requiredgroup=1,
            can_be_late=True,
            extension=".zip",
        )
        homework.save()

        required_groups = RequiredGroups(
            name=name,
            course=course,
            max_members=2,
            limit_date=DateTimeField().clean('2018-12-09 23:55')
        )
        required_groups.save()

        self.assertEquals(required_groups.name, name)


        #self.c.get('/customers/details/', {'name': 'fred', 'age': 7})