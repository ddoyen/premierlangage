#!/usr/bin/env python

from datetime import datetime

from jsonfield import JSONField
from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField
from django.utils import timezone
from loader.models import PLTP, PL, PLDM
from django.utils import timezone
from lti.models import LTIModel, LTIgrade
from loader.models import PLTP, PL
from playexo.enums import State

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'DM/homework_{0}/{1}/{2}'.format(instance.id_homework, instance.id_group, filename)


class Activity(LTIModel,LTIgrade):
    name = models.CharField(max_length=200, null=False)
    pltp = models.ForeignKey(PLTP, null=False, on_delete=models.CASCADE)
    open = models.BooleanField(null = False, default = True)
    open = models.BooleanField(null=False, default=True)

    def __str__(self):
        return str(self.id)+" "+self.name

class Deposit(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, null=False)
    file = models.FileField(upload_to=user_directory_path)
    date = models.DateTimeField(null=False, default=timezone.now)
    grade = models.IntegerField(null=True)
    id_group = models.IntegerField(null=True)
    id_homework = models.IntegerField(null=True)

    def __str__(self):
        return str(self.id)

class AnswerHomework(models.Model):
    id = models.AutoField(primary_key=True)
    deposits = models.ManyToManyField(Deposit, blank=True)
    id_group = models.IntegerField(null=True)
    name = models.CharField(max_length=200, null=True)

class Homework(models.Model):
    id = models.AutoField(primary_key=True)
    pldm = models.ForeignKey(PLDM, null=False, on_delete=models.CASCADE)
    open = models.BooleanField(null=False, default=True)
    name = models.CharField(max_length=200, null=False)
    date_deposit_end = models.DateTimeField(default=timezone.now, blank=True)
    deposit_number = models.IntegerField(null=True)
    deposit_size = models.IntegerField(null=True)
    id_requiredgroup = models.IntegerField(null=True)
    can_be_late = models.BooleanField(default=False)
    answers = models.ManyToManyField(AnswerHomework, blank=True)
    extension = models.CharField(max_length=100, null=False)

    def __str__(self):
        return str(self.id)+" "+self.name

class ActivityTest(models.Model):
    name = models.CharField(max_length=200, null=False)
    pltp = models.ForeignKey(PLTP, null=False, on_delete=models.CASCADE)
    date = models.DateTimeField(null=False, default=timezone.now)
    
    
    @staticmethod
    def delete_outdated():
        activities = ActivityTest.objects.get.all().sort_by("date")
        for activity in activities:
            if (datetime.utcnow() - activity.date) > timedelta(days=1):
                activity.delete()
            else:
                break
                
        
    def __str__(self):
        return self.name


class Answer(models.Model):
    STARTED = 'ST'
    FAILED = 'FA'
    SUCCEEDED = 'SU'
    NOT_STARTED = 'NS'
    STATE = (
        (STARTED, 'Commencé'),
        (FAILED, 'Echoué'),
        (SUCCEEDED, 'Réussi'),
    )
    
    value = JSONField()
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    pl = models.ForeignKey(PL, null=False, on_delete=models.CASCADE)
    seed = models.CharField(max_length=50, null=True)
    date = models.DateTimeField(null=False, default=timezone.now)
    grade = models.IntegerField(null=False)
    
    
    @staticmethod
    def last_seed(pl, user):
        answers = Answer.objects.filter(pl=pl, user=user).order_by("-date")
        return None if not answers else answers[0].seed
    


    @staticmethod
    def last_success(pl, user):
        answers = Answer.objects.filter(pl=pl, user=user).order_by("-date")
        # FIXME if last Answer grade is -1 this is no good
        return False if not answers else answers[0].grade > 0




    @staticmethod
    def last_answer(pl, user):
        answers = Answer.objects.filter(pl=pl, user=user).order_by("-date")
        if not answers:
            return None
        for answer in [i.value for i in answers]:
            if answer:
                return answer
        return None
    
    
    @staticmethod
    def pl_state(pl, user):
        """Return the state of the answer with the highest grade.
        Used to set the color state """
        answers = Answer.objects.filter(user=user, pl=pl).order_by("-grade")
        return State.by_grade(None if not answers else answers[0].grade)
    
    
    @staticmethod
    def pltp_state(pltp, user):
        """Return a list of tuples (pl_id, state) where state follow pl_state() rules."""
        return [(pl.id, Answer.pl_state(pl, user)) for pl in pltp.pl.all()] 
    
    
    @staticmethod
    def pltp_summary(pltp, user):
        """
            Give information about the PLTP's completion of this user as a dict of 5 lists:
            {
                'succeeded':   [ % succeeded, nbr succeeded],
                'part_succ':   [ % part_succ, nbr part_succ],
                'failed':      [ % failed, nbr failed],
                'started:      [ % started, nbr started],
                'not_started': [ % not started, nbr not started],
            }
        """
        
        state = {
            State.SUCCEEDED:   [0.0, 0],
            State.PART_SUCC:   [0.0, 0],
            State.FAILED:      [0.0, 0],
            State.STARTED:     [0.0, 0],
            State.NOT_STARTED: [0.0, 0],
        }
        
        for pl in pltp.pl.all():
            state[
                State.STARTED if Answer.pl_state(pl, user) in [State.TEACHER_EXC, State.SANDBOX_EXC] else Answer.pl_state(pl, user)
                ][1] += 1
            
        nb_pl = sum([state[k][1] for k in state]) 
        nb_pl = 1 if not nb_pl else nb_pl
        
        for k, v in state.items():
            state[k] = [str(state[k][1]*100/nb_pl), str(state[k][1])]
        
        return state
    
    
    @staticmethod
    def course_state(course):
        """ 
            Return every pltp state of every user of this course as a list of dicts:
            {
                'user_id': id,
                'pltp_sha1' sha1,
                'pl': list(pl_id, state)
            }
            where 'state' follow pl_state() rules.
        """
        
        lst = list()
        for user in course.user:
            dct = dict()
            dct['user_id'] = user.id
            for activity in course:
                dct['pltp_sha1'] = activity.pltp.sha1
                dct['pl'] = Answer.pltp_state(activity.pltp, user)
            lst.append(dct)
        
        return lst
    
    
    @staticmethod
    def user_course_summary(course, user):
        """
            Give information about the completion of every PL of this user in course as a dict of 5 tuples:
            {
                'succeeded':   [ % succeeded, nbr succeeded],
                'part_succ':   [ % part_succ, nbr part_succ],
                'failed':      [ % failed, nbr failed],
                'started:      [ % started, nbr started],
                'not_started': [ % not started, nbr not started],
            }
        """
    
        state = {
            State.SUCCEEDED:   [0.0, 0],
            State.PART_SUCC:   [0.0, 0],
            State.FAILED:      [0.0, 0],
            State.STARTED:     [0.0, 0],
            State.NOT_STARTED: [0.0, 0],
        }
        
        for activity in course.activity.all():
            summary = Answer.pltp_summary(activity.pltp, user)
            for k in summary:
                state[k][1] += int(summary[k][1])
        
        nb_pl = sum([state[k][1] for k in state]) 
        nb_pl = 1 if not nb_pl else nb_pl
        
        for k, v in state.items():
            state[k] = [str(state[k][1]*100/nb_pl), str(state[k][1])]
        
        return state
