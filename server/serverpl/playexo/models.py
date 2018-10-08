import time, logging

import htmlprint
from django.http import Http404
from django.shortcuts import get_object_or_404
from jsonfield import JSONField
from django.urls import resolve
from django.db import models, IntegrityError
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.utils import timezone
from django.dispatch import receiver
from django.template import Template, RequestContext
from django.template.loader import get_template

from lti.models import LTIModel
from loader.models import PLTP, PL
from playexo.enums import State
from playexo.request import SandboxBuild, SandboxEval
from classmanagement.models import Course


logger = logging.getLogger(__name__)



class Activity(LTIModel):
    name = models.CharField(max_length=200, null=False)
    open = models.BooleanField(default=True)
    pltp = models.ForeignKey(PLTP, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    
    
    @classmethod
    def get_or_create_from_lti(cls, request, lti_launch):
        """Creates an Activity corresponding to ID in the url and sets
        its course according to the LTI request..

        The corresponding Course must have already been created,
        Course.DoesNotExists will be raised otherwise.

        Returns a tuple of (object, created), where object is the
        retrieved or created object and created is a boolean specifying
        whether a new object was created."""
        course_id = lti_launch.get("context_id")
        consumer = lti_launch.get('oauth_consumer_key')
        activity_id = lti_launch.get('resource_link_id')
        activity_name = lti_launch.get('resource_link_title')
        if not all([course_id, activity_id, activity_name, consumer]):
            # TODO : Use BadRequest Exception
            raise Http404("Could not create Activity: on of these parameters are missing:"
                          + "[context_id, resource_link_id, resource_link_title, "
                            "oauth_consumer_key]")
        
        course = Course.objects.get(consumer_id=course_id, consumer=consumer)
        try:
            return cls.objects.get(consumer_id=activity_id, consumer=consumer), False
        except Activity.DoesNotExist:
            match = resolve(request.path)
            if not match.app_name or not match.url_name:
                match = None
            if not match or (match and match.app_name + ":" + match.url_name != "playexo:activity"):
                logger.warning(request.path + " does not correspond to 'playexo:activity' in "
                                              "Activity.get_or_create_from_lti")
                raise Http404("Activity could not be found.")
            parent = get_object_or_404(Activity, id=match.kwargs['activity_id'])
            new = Activity.objects.create(consumer_id=activity_id, consumer=consumer,
                                          name=activity_name, pltp=parent.pltp, course=course)
            return new, True
    
    
    def __str__(self):  # pragma: no cover
        return str(self.id) + " " + self.name



class SessionActivity(models.Model):
    """Represents the state of an activity for a given user.
    
    Parameters:
        user       - User corresponding to this session.
        activity   - Activity corresponding to this session.
        current_pl - Which PL is currently loaded (None if the PLTP is loaded)."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    current_pl = models.ForeignKey(PL, on_delete=models.CASCADE, null=True)
    
    class Meta:
        unique_together = ('user', 'activity')
    
    def exercise(self, pl=...):
        """Return the SessionExercice corresponding to self.current_pl.
        
        If the optionnal parameter 'pl' is given (can be given as None for the PLTP), will instead
        return the SessionExercice corresponding to pl.
        
        Raise IntegrityError if no session for either self.current_pl or pl (if given) was found."""
        try:
            return next(
                    i for i in self.sessionexercise_set.all()
                    if i.pl == (self.current_pl if pl is ... else pl)
            )
        except StopIteration:
            raise IntegrityError("'current_pl' of SessionActivity does not have a corresponding "
                                 + "SessionExercise.")



class SessionExerciseAbstract(models.Model):
    """Abstract class to represent the state of a PL for a given user.
    
    Parameters:
        pl      - PL corresponding to this session (None if it's the PLTP session).
        built   - Whether the session is built (True), or need to be built (False).
        envid   - Must contains the ID of the environment on the sandbox if the session is built.
        context - Dictionnary of the PL (or PLTP)."""
    
    pl = models.ForeignKey(PL, on_delete=models.CASCADE, null=True)
    built = models.BooleanField(default=False)
    envid = models.CharField(max_length=300, null=True)
    context = JSONField(null=True)
    
    class Meta:
        abstract = True
    
    # TODO: Allowing to add key with the PL syntax (dict1.dict2.val)
    def add_to_context(self, key, value):
        """Add value corresponding to key in the context."""
        self.context[key] = value
        self.save()
    
    
    def get_from_context(self, key):
        """Get key from context.

        Return False is key does not exists.

        Does implement syntax of PL for nested dict. I.E.: 'dict1.dict2.[...].dictn.val' will return
        'context['dict1']['dict2']...['dictn']['val']"""
        try:
            if '.' in key:
                val = self.context
                for k in key.split('.'):
                    val = val[k]
            else:
                val = self.context[key]
        except KeyError:
            return False
        return val
    
    
    def evaluate(self, request, answers, test=False):
        """Evaluate the exercise with the given answers according to the current context.
        
        Parameters:
            request - (django.http.request) Current Django request object.
            answers - (dict) Answers of the student.
            test    - (bool) Whether this exercise is in a testing session or not.
        """
        context = {}
        evaluator = SandboxEval(self.envid, answers)
        if not evaluator.check():
            self.build(request, test=test)
            evaluator = SandboxEval(self.envid, answers)
        
        response = evaluator.call()
        answer = {
            "answers": answers,
            "user"   : request.user,
            "pl"     : self.pl,
            "grade"  : response['grade'],
        }
        
        if response['status'] < 0:  # Sandbox Error
            feedback = response['feedback']
            if request.user.profile.can_load() and response['sandboxerr']:
                feedback += "<br><hr>Sandbox error:<br>" + htmlprint.code(response['sandboxerr'])
                feedback += "<br><hr>Received on stderr:<br>" + htmlprint.code(response['stderr'])
        
        elif response['status'] > 0:  # Evaluator Error
            feedback = ("Une erreur s'est produite lors de l'exécution du script d'évaluation "
                        + ("(exit code: %d, env: %s). Merci de prévenir votre professeur"
                           % (response['status'], response['id'])))
            if request.user.profile.can_load():
                feedback += "<br><hr>Received on stderr:<br>" + htmlprint.code(response['stderr'])
        
        else:  # Success
            context = dict(response['context'])
            feedback = response['feedback']
            if request.user.profile.can_load() and response['stderr']:
                feedback += "<br><hr>Received on stderr:<br>" + htmlprint.code(response['stderr'])
            answer["seed"] = context['seed'],
        
        keys = list(response.keys())
        for key in keys:
            response[key + "__"] = response[key]
        for key in keys:
            del response[key]
        del response['context__']
        context.update(response)
        
        dic = dict(self.context)
        dic.update(context)
        dic['answers__'] = answers
        
        return answer, feedback, dic
    
    
    def build(self, request, test=False):
        """Build the exercise with the given according to the current context.
        
        Parameters:
            request - (django.http.request) Current Django request object.
            test    - (bool) Whether this exercise is in a testing session or not.
        """
        response = SandboxBuild(dict(self.context), test=test).call()
        
        if response['status'] < 0:
            msg = ("Une erreur s'est produit sur la sandbox (exit code: %d, env: %s)."
                   + " Merci de prévenir votre professeur.") % (response['status'], response['id'])
            if request.user.profile.can_load():
                msg += "<br><br>" + htmlprint.code(response['sandboxerr'])
            raise Exception(msg)
        
        if response['status'] > 0:
            msg = ("Une erreur s'est produite lors de l'exécution du script before/build "
                   + ("(exit code: %d, env: %s). Merci de prévenir votre professeur"
                      % (response['status'], response['id'])))
            if request.user.profile.can_load() and response['stderr']:
                msg += "<br><br>Reçu sur stderr:<br>" + htmlprint.code(response['stderr'])
            raise Exception(msg)
        
        context = dict(response['context'])
        keys = list(response.keys())
        for key in keys:
            response[key + "__"] = response[key]
        for key in keys:
            del response[key]
        del response['context__']
        
        context.update(response)
        self.envid = response['id__']
        self.context.update(context)
        self.built = True
        self.save()



class SessionExercise(SessionExerciseAbstract):
    """Class representing the state of a PL inside of a SessionActivity.
    
    Parameters:
        pl      - PL corresponding to this session (None if it's the PLTP session).
        built   - Whether the session is built (True), or need to be built (False).
        envid   - Must contains the ID of the environment on the sandbox if the session is built.
        context - Dictionnary of the PL (or PLTP).
        activity_session - SessionActivity to which this SessionExercise belong."""
    activity_session = models.ForeignKey(SessionActivity, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('pl', 'activity_session')
    
    @receiver(post_save, sender=SessionActivity)
    def create_session_exercise(sender, instance, created, **kwargs):
        """When an ActivitySession is created, automatically create a SessionExercise for the PLTP
        and every PL."""
        if created:
            for pl in instance.activity.pltp.pl.all():
                SessionExercise.objects.create(activity_session=instance, pl=pl)
            SessionExercise.objects.create(activity_session=instance)  # For the pltp
    
    
    def save(self, *args, **kwargs):
        """Automatically add the PL/PLTP json content to the context if context is empty when
        saving."""
        if not self.context:
            if self.pl:
                self.context = dict(self.pl.json)
            else:
                self.context = dict(self.activity_session.activity.pltp.json)
            self.context['activity_id__'] = self.activity_session.activity.id
        super().save(*args, **kwargs)
    
    
    def reroll(self, grade=None, seed=None):
        """Return whether the seed must be reroll (True) or not (False)."""
        if grade:
            return grade != 100
        oneshot = self.get_from_context('settings.oneshot')
        return not seed or oneshot
    
    
    def get_pl(self, request, context):
        """Return a template of the PL rendered with context."""
        pl = self.pl
        highest_grade = Answer.highest_grade(pl, self.activity_session.user)
        last = Answer.last(pl, self.activity_session.user)
        
        seed = last.seed if last else None
        if self.reroll(highest_grade.grade, seed):
            seed = time.time()
            self.built = False
        self.add_to_context('seed', seed)
        
        predic = {
            'user_settings__': self.activity_session.user.profile,
            'user__'         : self.activity_session.user,
            'pl_id__'        : pl.id,
            'answers__'      : last.answers if last else {},
            'grade__'        : highest_grade.grade if highest_grade else None,
        }
        
        if not self.built:
            self.build(request)
        dic = dict(self.context if not context else context)
        dic.update(predic)
        
        for key in dic:
            if type(dic[key]) is str:
                dic[key] = Template(dic[key]).render(RequestContext(request, dic))
        
        return get_template("playexo/pl.html").render(dic, request)
    
    
    def get_exercise(self, request, context=None):
        """Return a template of the PL or the PLTP rendered with self.context.
         
        If given, will use context instead."""
        try:
            pl = self.pl
            if pl:
                return self.get_pl(request, context)
            else:
                dic = dict(self.context if not context else context)
                dic['user_settings__'] = self.activity_session.user.profile
                dic['user__'] = self.activity_session.user
                dic['first_pl__'] = self.activity_session.activity.pltp.pl.all()[0].id
                for key in dic:
                    if type(dic[key]) is str:
                        dic[key] = Template(dic[key]).render(RequestContext(request, dic))
                return get_template("playexo/pltp.html").render(dic, request)
        
        except Exception as e:
            error_msg = str(e)
            if request.user.profile.can_load():
                error_msg += "<br><br>" + htmlprint.html_exc()
            return get_template("playexo/error.html").render({"error_msg": error_msg})
    
    
    def get_navigation(self, request, context=None):
        pl_list = [{
            'id'   : None,
            'state': None,
            'title': self.activity_session.activity.pltp.json['title'],
        }]
        for pl in self.activity_session.activity.pltp.pl.all():
            pl_list.append({
                'id'   : pl.id,
                'state': Answer.pl_state(pl, self.activity_session.user),
                'title': pl.json['title'],
            })
        context = dict(self.context if not context else context)
        context.update({
            "pl_list__": pl_list,
            'pl_id__'  : self.pl.id if self.pl else None
        })
        return get_template("playexo/navigation.html").render(context, request)
    
    
    def get_context(self, request, context=None):
        return {
            "navigation": self.get_navigation(request, context),
            "exercise"  : self.get_exercise(request, context),
        }



class SessionTest(SessionExerciseAbstract):
    """Class representing the state of a PL inside of a SessionActivity.
    
    Parameters:
        pl      - PL corresponding to this session.
        built   - Whether the session is built (True), or need to be built (False).
        envid   - Must contains the ID of the environment on the sandbox if the session is built.
        context - Dictionnary of the PL (or PLTP).
        user    - User currently testing a PL.
        date    - Date of the creation of the session.
        
    When the number of session for an user exceed MAX_SESSION_PER_USER, older session are deleted.
    """
    MAX_SESSION_PER_USER = 100
    
    pl = models.ForeignKey(PL, on_delete=models.CASCADE, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    date = models.DateTimeField(default=timezone.now, null=False)
    
    
    def save(self, *args, **kwargs):
        """Automatically add the PL's json content to the context if context is empty when
        saving. Will also delete outdated session."""
        if not self.context:
            self.context = dict(self.pl.json)
        
        q = SessionTest.objects.filter(user=self.user).order_by("-date")
        if len(q) >= self.MAX_SESSION_PER_USER:
            for elem in q[self.MAX_SESSION_PER_USER:]:
                elem.delete()
        
        super().save(*args, **kwargs)
    
    
    def delete(self, *args, **kwargs):
        """Delete the corresponding PL when the session is deleted."""
        self.pl.delete()
        super().delete(*args, **kwargs)
    
    
    def get_pl(self, request, context, answer=None):
        """Return a template of the PL rendered with context.
        
        If answer is given, will determine if the seed must be reroll base on its grade."""
        pl = self.pl
        seed = None
        if answer['grade'] < 100 if answer else True:
            seed = time.time()
            self.built = False
        self.add_to_context('seed', seed)
        
        predic = {
            'user_settings__': self.user.profile,
            'session__'      : self,
            'user__'         : self.user,
            'pl_id__'        : pl.id,
        }
        
        if not self.built:
            self.build(request, test=True)
        dic = dict(self.context if not context else context)
        dic.update(predic)
        
        for key in dic:
            if type(dic[key]) is str:
                dic[key] = Template(dic[key]).render(RequestContext(request, dic))
        return get_template("playexo/preview.html").render(dic, request)
    
    
    def get_exercise(self, request, context=None, answer=None):
        """Return a template of the PL or the PLTP rendered with self.context.
        
        If given, will use context instead.
        If answer is given, will determine if the seed must be reroll base on its grade."""
        try:
            return self.get_pl(request, context, answer)
        except Exception as e:
            error_msg = str(e)
            if request.user.profile.can_load():
                error_msg += "<br><br>" + htmlprint.html_exc()
            return get_template("playexo/error.html").render({"error_msg": error_msg})



class Answer(models.Model):
    answers = JSONField(default='{}')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pl = models.ForeignKey(PL, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, null=True, on_delete=models.CASCADE)
    seed = models.CharField(max_length=100, default=time.time)
    date = models.DateTimeField(default=timezone.now)
    grade = models.IntegerField(null=True)
    
    
    @staticmethod
    def highest_grade(pl, user):
        answers = Answer.objects.filter(pl=pl, user=user).order_by("-grade")
        return answers[0] if answers else None
    
    
    @staticmethod
    def last(pl, user):
        answers = Answer.objects.filter(pl=pl, user=user).order_by("-date")
        return None if not answers else answers[0]
    
    
    @staticmethod
    def pl_state(pl, user):
        """Return the state of the answer with the highest grade."""
        answers = Answer.objects.filter(user=user, pl=pl).order_by("-grade")
        return State.by_grade(answers[0].grade if answers else ...)
    
    
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
                'error':       [ % error, nbr error],
            }
            
            All data are strings."""
        state = {
            State.SUCCEEDED  : [0.0, 0],
            State.PART_SUCC  : [0.0, 0],
            State.FAILED     : [0.0, 0],
            State.STARTED    : [0.0, 0],
            State.NOT_STARTED: [0.0, 0],
            State.ERROR      : [0.0, 0],
        }
        
        for pl in pltp.pl.all():
            state[Answer.pl_state(pl, user)][1] += 1
        
        nb_pl = max(sum([state[k][1] for k in state]), 1)
        for k, v in state.items():
            state[k] = [str(state[k][1] * 100 / nb_pl), str(state[k][1])]
        
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
        """Give information about the completion of every PL of this
            user in course as a dict of 5 tuples:
            {
                'succeeded':   [ % succeeded, nbr succeeded],
                'part_succ':   [ % part_succ, nbr part_succ],
                'failed':      [ % failed, nbr failed],
                'started:      [ % started, nbr started],
                'not_started': [ % not started, nbr not started],
                'error':       [ % error, nbr error],
            }
            
            All data are strings."""
        state = {
            State.SUCCEEDED  : [0.0, 0],
            State.PART_SUCC  : [0.0, 0],
            State.FAILED     : [0.0, 0],
            State.STARTED    : [0.0, 0],
            State.NOT_STARTED: [0.0, 0],
            State.ERROR      : [0.0, 0],
        }
        
        for activity in course.activity_set.all():
            summary = Answer.pltp_summary(activity.pltp, user)
            for k in summary:
                state[k][1] += int(summary[k][1])
        
        nb_pl = max(sum([state[k][1] for k in state]), 1)
        for k, v in state.items():
            state[k] = [str(state[k][1] * 100 / nb_pl), str(state[k][1])]
        
        return state
