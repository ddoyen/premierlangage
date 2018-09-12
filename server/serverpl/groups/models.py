from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from classmanagement.models import Course

class Groups(models.Model):
    id = models.AutoField(primary_key=True)
    password = models.CharField(max_length=1024, blank=True)
    name = models.CharField(max_length=1024)
    max_members = models.IntegerField(null=True)
    creation_date = models.DateTimeField(default=timezone.now, blank=True)
    students = models.ManyToManyField(User, blank=True, related_name="students")

    def __str__(self):
        return 'Group name : ' + self.name + '\nCreation date : ' + str(self.creation_date)


class RequiredGroups(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=1024, blank=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=False)
    max_members = models.IntegerField(null=True)
    limit_date = models.DateTimeField(default=timezone.now, blank=True)
    groups = models.ManyToManyField(Groups, blank=True, related_name="groups")

    def __str__(self):
        return 'test'








