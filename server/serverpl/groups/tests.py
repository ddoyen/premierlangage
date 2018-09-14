#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  test_parsers.py
#
#  Copyright 2018 Coumes Quentin <qcoumes@etud.u-pem.fr>
#

import shutil
import json

from os.path import join, isdir, isfile

from django.test import TestCase, Client, override_settings
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.messages import constants as messages
from django.forms.fields import DateTimeField

from groups.models import Groups, RequiredGroups
from playexo.models import Homework, Deposit
from classmanagement.models import Course
from loader.models import PLDM

FAKE_FB_ROOT = join(settings.BASE_DIR, 'groups/tests/ressources')


@override_settings(FILEBROWSER_ROOT=FAKE_FB_ROOT)
class GroupsTestCase(TestCase):
    @classmethod

    def setUpTestData(self):
        self.teacher = User.objects.create_user(username='teacher', password='12345', id=101)
        self.cTeacher = Client()
        self.cTeacher.force_login(self.teacher, backend=settings.AUTHENTICATION_BACKENDS[0])

        self.user1 = User.objects.create_user(username='user1', password='12345', id=102)
        self.c1 = Client()
        self.c1.force_login(self.user1, backend=settings.AUTHENTICATION_BACKENDS[0])

        self.user2 = User.objects.create_user(username='user2', password='12345', id=103)
        self.c2 = Client()
        self.c2.force_login(self.user2, backend=settings.AUTHENTICATION_BACKENDS[0])

        self.user3 = User.objects.create_user(username='user3', password='12345', id=104)
        self.c3 = Client()
        self.c3.force_login(self.user3, backend=settings.AUTHENTICATION_BACKENDS[0])

        self.user4 = User.objects.create_user(username='user4', password='12345', id=105)
        self.c4 = Client()
        self.c4.force_login(self.user4, backend=settings.AUTHENTICATION_BACKENDS[0])

        self.user5 = User.objects.create_user(username='user5', password='12345', id=106)
        self.c5 = Client()
        self.c5.force_login(self.user5, backend=settings.AUTHENTICATION_BACKENDS[0])

        self.user6 = User.objects.create_user(username='user6', password='12345', id=107)
        self.c6 = Client()
        self.c6.force_login(self.user6, backend=settings.AUTHENTICATION_BACKENDS[0])

    def testCreateGroupWithPassword(self):
        course = Course(id="1", name='Prog C', label="TEST")
        course.save()

        course.teacher.add(self.teacher)
        course.student.add(self.user1)
        course.student.add(self.user2)
        course.student.add(self.user3)
        course.student.add(self.user4)
        course.student.add(self.user5)
        course.student.add(self.user6)

        name = 'String in C'

        data = {
            "name": {
                "name": "test",
                "name": "test"
            }
        }

        pldm = PLDM(
            sha1="test1234",
            name=name,
            rel_path='/test_scenario_groups',
            json=json.dumps(data)
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

        response = self.c3.get('/groups/group/creategroup/', {
            'id_required_groups': required_groups.id,
            'max_members': 2,
            'password': '1234',
        })
        self.assertEqual(response.status_code, 302)

        response = self.c4.get('/groups/group/joingroup/', {
            'id_required_groups': required_groups.id,
            'id': 1,
            'password': '1234',
        })
        self.assertEqual(response.status_code, 302)

        g = required_groups.groups.all()[0]
        self.assertEquals(g.students.all()[0], self.user3)
        self.assertEquals(g.students.all()[1], self.user4)

    def testCreateGroupWithoutPassword(self):
        course = Course(id="1", name='Prog C', label="TEST")
        course.save()

        course.teacher.add(self.teacher)
        course.student.add(self.user1)
        course.student.add(self.user2)
        course.student.add(self.user3)
        course.student.add(self.user4)
        course.student.add(self.user5)
        course.student.add(self.user6)

        name = 'String in C'

        data = {
            "name": {
                "name": "test",
                "name": "test"
            }
        }

        pldm = PLDM(
            sha1="test1234",
            name=name,
            rel_path='/test_scenario_groups',
            json=json.dumps(data)
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

        # Creation of the first group withoout password
        response = self.c1.get('/groups/group/creategroup/', {
            'id_required_groups': required_groups.id,
            'max_members': 2,
            'password': ''
        })
        self.assertEqual(response.status_code, 302)

        response = self.c2.get('/groups/group/joingroup/', {
            'id_required_groups': required_groups.id,
            'id': 1,
            'password': '',
        })
        self.assertEqual(response.status_code, 302)

        g = required_groups.groups.all()[0]
        self.assertEquals(g.students.all()[0], self.user1)
        self.assertEquals(g.students.all()[1], self.user2)

    def testScenario(self):
        course = Course(id="1", name='Prog C', label="TEST")
        course.save()

        course.teacher.add(self.teacher)
        course.student.add(self.user1)
        course.student.add(self.user2)
        course.student.add(self.user3)
        course.student.add(self.user4)
        course.student.add(self.user5)
        course.student.add(self.user6)
        course.save()

        name = 'String in C'

        data = {
            "name": {
                "name": "test",
                "name": "test"
            }
        }

        pldm = PLDM(
            sha1 = "test1234",
            name = name,
            rel_path = '/test_scenario_groups',
            json= json.dumps(data)
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

        # Creation of the first group withoout password
        response = self.c1.get('/groups/group/creategroup/', {
            'id_required_groups': required_groups.id,
            'max_members': 2,
            'password': ''
        })
        self.assertEqual(response.status_code, 302)

        response = self.c2.get('/groups/group/joingroup/', {
            'id_required_groups': required_groups.id,
            'id': 1,
            'password':'',
        })
        self.assertEqual(response.status_code, 302)

        g = required_groups.groups.all()[0]
        self.assertEquals(g.students.all()[0], self.user1)
        self.assertEquals(g.students.all()[1], self.user2)

        # Creation of the 2nd group with a password
        response = self.c3.get('/groups/group/creategroup/', {
            'id_required_groups': required_groups.id,
            'max_members': 2,
            'password': '1234',
        })
        self.assertEqual(response.status_code, 302)

        response = self.c4.get('/groups/group/joingroup/', {
            'id_required_groups': required_groups.id,
            'id': 2,
            'password': '1234',
        })
        self.assertEqual(response.status_code, 302)

        g = required_groups.groups.all()[1]
        self.assertEquals(g.students.all()[0], self.user3)
        self.assertEquals(g.students.all()[1], self.user4)

        # Creation of a third group without password
        response = self.cTeacher.get('/groups/group/creategroup_admin/', {
            'name': 'Group Test',
            'id_required_groups': required_groups.id,
            'max_members': 2,
            'password': ''
        })
        self.assertEqual(response.status_code, 302)

        response = self.cTeacher.get('/groups/group/joingroup_admin/', {
            'id_required_groups': required_groups.id,
            'id': 3,
            'id_user': self.user5.id,
        })

        response = self.cTeacher.get('/groups/group/joingroup_admin/', {
            'id_required_groups': required_groups.id,
            'id': 3,
            'id_user': self.user6.id,
        })
        self.assertEqual(response.status_code, 302)

        g = required_groups.groups.all()[2]
        self.assertEquals(g.students.all()[0], self.user5)
        self.assertEquals(g.students.all()[1], self.user6)


    def testNotation(self):
        course = Course(id="1", name='Prog C', label="TEST")
        course.save()

        course.teacher.add(self.teacher)
        course.student.add(self.user1)
        course.student.add(self.user2)
        course.student.add(self.user3)
        course.student.add(self.user4)
        course.student.add(self.user5)
        course.student.add(self.user6)
        course.save()

        name = 'String in C'

        data = {
            "name": {
                "name": "test",
                "name": "test"
            }
        }

        pldm = PLDM(
            sha1 = "test1234",
            name = name,
            rel_path = '/test_scenario_groups',
            json= json.dumps(data)
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

        # Creation of the first group withoout password
        response = self.c1.get('/groups/group/creategroup/', {
            'id_required_groups': required_groups.id,
            'max_members': 2,
            'password': ''
        })
        self.assertEqual(response.status_code, 302)

        response = self.c2.get('/groups/group/joingroup/', {
            'id_required_groups': required_groups.id,
            'id': 1,
            'password':'',
        })
        self.assertEqual(response.status_code, 302)

        g = required_groups.groups.all()[0]
        self.assertEquals(g.students.all()[0], self.user1)
        self.assertEquals(g.students.all()[1], self.user2)

        # Creation of the 2nd group with a password
        response = self.c3.get('/groups/group/creategroup/', {
            'id_required_groups': required_groups.id,
            'max_members': 2,
            'password': '1234',
        })
        self.assertEqual(response.status_code, 302)

        response = self.c4.get('/groups/group/joingroup/', {
            'id_required_groups': required_groups.id,
            'id': 2,
            'password': '1234',
        })
        self.assertEqual(response.status_code, 302)

        g = required_groups.groups.all()[1]
        self.assertEqual(g.students.all()[0], self.user3)
        self.assertEqual(g.students.all()[1], self.user4)

        # Creation of a third group without password
        response = self.cTeacher.get('/groups/group/creategroup_admin/', {
            'name': 'Group Test',
            'id_required_groups': required_groups.id,
            'max_members': 2,
            'password': ''
        })
        self.assertEqual(response.status_code, 302)

        response = self.cTeacher.get('/groups/group/joingroup_admin/', {
            'id_required_groups': required_groups.id,
            'id': 3,
            'id_user': self.user5.id,
        })

        response = self.cTeacher.get('/groups/group/joingroup_admin/', {
            'id_required_groups': required_groups.id,
            'id': 3,
            'id_user': self.user6.id,
        })
        self.assertEqual(response.status_code, 302)

        g = required_groups.groups.all()[2]
        self.assertEqual(g.students.all()[0], self.user5)
        self.assertEqual(g.students.all()[1], self.user6)


        deposit = Deposit(
            name='test',
            id_group=1,
            id_homework=1,
        )
        deposit.save()

        response = self.cTeacher.get('/courses/course/evaluate/', {
            'id_deposit': 1,
            'id_homework': 1,
            'grade': 10,
        })

        deposit = Deposit.objects.get(id=deposit.id)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(deposit.grade, 10)


    def testJoinWithBadPassword(self):
        course = Course(id="1", name='Prog C', label="TEST")
        course.save()

        course.teacher.add(self.teacher)
        course.student.add(self.user1)
        course.student.add(self.user2)
        course.student.add(self.user3)
        course.student.add(self.user4)
        course.student.add(self.user5)
        course.student.add(self.user6)
        course.save()

        name = 'String in C'

        data = {
            "name": {
                "name": "test",
                "name": "test"
            }
        }

        pldm = PLDM(
            sha1="test1234",
            name=name,
            rel_path='/test_scenario_groups',
            json=json.dumps(data)
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

        # Creation of the first group withoout password
        response = self.c1.get('/groups/group/creategroup/', {
            'id_required_groups': required_groups.id,
            'max_members': 2,
            'password': 'test'
        })
        self.assertEqual(response.status_code, 302)

        response = self.c2.get('/groups/group/joingroup/', {
            'id_required_groups': required_groups.id,
            'id': 1,
            'password': 'False',
        })
        self.assertEqual(response.status_code, 302)

        g = required_groups.groups.all()[0]
        self.assertEqual(1, len(g.students.all()))


    def testBadRequest(self):
        try:
            course = Course(id="1", name='Prog C', label="TEST")
            course.save()

            course.teacher.add(self.teacher)
            course.student.add(self.user1)
            course.student.add(self.user2)
            course.student.add(self.user3)
            course.student.add(self.user4)
            course.student.add(self.user5)
            course.student.add(self.user6)
            course.save()

            name = 'String in C'

            data = {
                "name": {
                    "name": "test",
                    "name": "test"
                }
            }

            pldm = PLDM(
                sha1="test1234",
                name=name,
                rel_path='/test_scenario_groups',
                json=json.dumps(data)
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

            # Creation of the first group withoout password
            response = self.c1.get('/groups/group/creategroup/', {
                'id_required_groups': 100,
                'max_members': 2,
                'password': 'test'
            })
            self.assertEqual(response.status_code, 404)

        except AssertionError:
            m = list(response.context['messages'])
            if m:
                print("\nFound messages:")
                [print(i.level,':',i.message) for i in m]
            raise










