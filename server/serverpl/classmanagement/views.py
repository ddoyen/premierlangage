#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python [Version]
#
#  Author: Coumes Quentin     Mail: qcoumes@etud.u-pem.fr
#  Created: 2017-07-30
#  Last Modified: 2017-07-30


import logging

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponse
from datetime import datetime, timezone
import os
import zipfile
from io import StringIO
from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import json
from classmanagement.models import Course
from groups.models import RequiredGroups, Groups
from playexo.models import Answer, Activity, Homework, AnswerHomework
from playexo.views import activity_receiver
from playexo.enums import State


logger = logging.getLogger(__name__)


@login_required
@csrf_exempt
def index(request):
    course = list()
    for item in request.user.course_set.all():
        summary = Answer.user_course_summary(item, request.user)
        completion = [{'name': "", 'count': summary[key][1], 'class': key.template} for key in summary]
        
        course.append({
            'id': item.id,
            'name': item.name,
            'completion': completion,
            'nb_square': sum([int(summary[key][1]) for key in summary])
        })
        
    return render(request, 'classmanagement/index.html', {'course': course})



@csrf_exempt
@login_required
def course_view(request, id):
    try:
        course = Course.objects.get(id=id)
    except:
        raise Http404("Course (id: "+str(id)+") not found.")
    if not course.is_member(request.user) and not request.user.profile.is_admin():
        logger.warning("User '"+request.user.username+"' denied to access course'"+course.name+"'.")
        raise PermissionDenied("Vous n'êtes pas membre de cette classe.")
    
    if request.method == 'GET':
        if request.GET.get("action", None) == "toggle_activity":
            if not request.user in course.teacher.all():
                logger.warning("User '"+request.user.username+"' denied to toggle course state'"+course.name+"'.")
                raise PermissionDenied("Vous n'avez pas les droits nécessaires pour fermer/ouvrir cette activité.")
            try:
                act = Activity.objects.get(id=request.GET.get("id", None))
                act.open = not act.open
                act.save()
                logger.info("User '"+request.user.username+"' set activity '"+act.name+"' 'open' attribute to '"+str(act.open)+"' in '"+course.name+"'.")
            except:
                raise Http404("L'activité d'ID '"+str(request.GET.get("id", None))+"' introuvable.")
    
    activity = list()
    for item in course.activity.all().order_by("id"):
        pl = [
            {
                'name': elem.json['title'],
                'state': Answer.pl_state(elem, request.user)
            }
            for elem in item.pltp.pl.all()
        ]
        
        
        len_pl = len(pl) if len(pl) else 1
        activity.append({
            'name': item.name,
            'pltp_sha1': item.pltp.sha1,
            'title': item.pltp.json['title'],
            'pl': pl,
            'id': item.id,
            'open': item.open,
            'width':str(100/len_pl),
        })

    homework = list()
    for item in course.homework.all().order_by("id"):
        homework.append(item)

    return render(request, 'classmanagement/course.html', {
        'homework': homework,
        'name': course.name,
        'activity': activity,
        'teacher': course.teacher.all(),
        'instructor': True if request.user in course.teacher.all() else False,
        'course_id': id,
    })



@csrf_exempt
@login_required
def course_summary(request, id):
    try:
        course = Course.objects.get(id=id)
    except:
        raise Http404("Impossible d'accéder à la page, cette classe n'existe pas.")
    if not request.user in course.teacher.all():
        logger.warning("User '"+request.user.username+"' denied to access summary of course'"+course.name+"'.")
        raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
    
    activities = course.activity.all().order_by("id")
    student = list()
    for user in course.student.all():
        tp = list()
        for activity in activities:
            summary = Answer.pltp_summary(activity.pltp, user)
            tp.append({
                'state': [{
                        'percent':summary[i][0],
                        'count':  summary[i][1],
                        'class':  i.template
                    }
                    for i in summary
                ],
                'name': activity.pltp.json['title'],
                'activity_name': activity.name,
            })
        student.append({
            'lastname': user.last_name,
            'object': user,
            'id': user.id,
            'activities': tp,
        })
    
    #Sort list by student's name
    student = sorted(student, key=lambda k: k['lastname'])
    
    return render(request, 'classmanagement/course_summary.html', {
        'state': [i for i in State if i not in [State.TEACHER_EXC, State.SANDBOX_EXC]],
        'name': course.name,
        'student': student,
        'range_tp': range(len(activities)),
        'course_id': id,
    })



@csrf_exempt
@login_required
def activity_summary(request, id, name):
    try:
        course = Course.objects.get(id=id)
    except:
        raise Http404("Impossible d'accéder à la page, cette classe n'existe pas.")
    if request.user not in course.teacher.all():
        logger.warning("User '"+request.user.username+"' denied to access summary of course'"+course.name+"'.")
        raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
    
    activity = Activity.objects.get(name=name)
    student = list()
    for user in course.student.all():
        tp = list()
        for pl in activity.pltp.pl.all():
            tp.append({
                'name': pl.json['title'],
                'state': Answer.pl_state(pl, user)
            })
        student.append({
            'lastname': user.last_name,
            'object': user,
            'id': user.id,
            'question': tp,
        })
    
    #Sort list by student's name
    student = sorted(student, key=lambda k: k['lastname'])
    
    return render(request, 'classmanagement/activity_summary.html', {
        'state': [i for i in State if i not in [State.TEACHER_EXC, State.SANDBOX_EXC]],
        'course_name': course.name,
        'activity_name': activity.name,
        'student': student,
        'range_tp': range(len(activity.pltp.pl.all())),
        'course_id': id,
    })



@csrf_exempt
@login_required
def student_summary(request, course_id, student_id):
    try:
        course = Course.objects.get(id=course_id)
    except:
        raise Http404("Impossible d'accéder à la page, cette classe n'existe pas.")
    if request.user not in course.teacher.all():
        logger.warning("User '"+request.user.username+"' denied to access summary of course'"+course.name+"'.")
        raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
        
    student = User.objects.get(id=student_id)
    activities = course.activity.all().order_by("id")
    
    tp = list()
    for activity in activities:
        question = list()
        for pl in activity.pltp.pl.all():
            state = Answer.pl_state(pl, student)
            question.append({
                'state': state,
                'name':  pl.json['title'],
            })
        len_tp = len(question) if len(question) else 1
        tp.append({
            'name': activity.pltp.json['title'],
            'activity_name': activity.name,
            'width': str(100/len_tp),
            'pl': question,
        })
        
    return render(request, 'classmanagement/student_summary.html', {
        'state': [i for i in State if i not in [State.TEACHER_EXC, State.SANDBOX_EXC]],
        'course_name': course.name,
        'student': student,
        'activities': tp,
        'course_id': course_id,
    })
    
    
@login_required
def redirect_activity(request, activity_id):
    request.session['current_activity'] = activity_id
    request.session['current_pl'] = None
    request.session['testing'] = False
    return HttpResponseRedirect(reverse(activity_receiver))

@login_required
def homework_summary(request):
    id = request.GET['id']
    if not id:
        return HttpResponseBadRequest("Missing 'id' parameter")
    try:
        homework = Homework.objects.get(id=id)
    except:
        raise Http404("Impossible d'accéder à la page, ce devoir n'existe pas.")
    group_id = None
    in_group = False
    required_groups = RequiredGroups.objects.get(id=homework.id_requiredgroup)
    is_teacher = False
    if request.user in required_groups.course.teacher.all():
        is_teacher = True
    for group in required_groups.groups.all():
        if request.user in group.students.all():
            group_id = group.id
            in_group = True
            break

    deposit = False
    answers = list()
    for answer in homework.answers.all():
        homeworks = homework.answers.filter(id_group=answer.id_group)
        group = Groups.objects.get(id=homeworks[0].id_group)
        if request.user in group.students.all():
            deposit = True
            for item in homeworks:
                answers.extend([item])
            break

    today = datetime.now(timezone.utc)
    can_deposit = today < homework.date_deposit_end
    if can_deposit:
        remaining_time = homework.date_deposit_end - today
    else:
        remaining_time = today - homework.date_deposit_end

    return render(request, 'classmanagement/homework_summary.html', {
        'answers': answers,
        'deposit': deposit,
        'is_teacher': is_teacher,
        'group_id': group_id,
        'remaining_time': remaining_time,
        'can_deposit': can_deposit,
        'homework': homework,
        'in_group': in_group,
    })


def new_name(lst):
    students = []
    for student in lst:
        students.append(student.username)
    name = '_'.join(students)
    return name

@login_required
def upload_file(request):
    id_homework = request.POST.get('id_homework', "")
    id_requiredgroup = request.POST.get('id_requiredgroup', "")
    rg = RequiredGroups.objects.get(id=id_requiredgroup)
    for group in rg.groups.all():
        if request.user in group.students.all():
            id_group = group.id
            break
    homework = Homework.objects.get(id=id_homework)

    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        group = Groups.objects.get(id=id_group)
        fs = AnswerHomework(id_group=id_group, name=new_name(group.students.all()))
        fs.save()
        filename = fs.file.save(myfile.name, myfile)
        fs.save()
        homework.answers.add(fs)
        homework.save()
        return redirect('/courses/course/homework/?id=' + id_homework)
    return redirect('/courses/course/homework/?id=' + id_homework)


@login_required
def notation(request):
    id = request.GET['id']
    homework = Homework.objects.get(id=id)
    rg = RequiredGroups.objects.get(id=homework.id_requiredgroup)
    if request.user not in rg.course.teacher.all():
        logger.warning(
            "User '" + request.user.username + "' denied to access all homework'" + rg.course.name + "'.")
        raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
    to_ignore = list()
    dic = list()
    id_homework = homework.id
    for answer in homework.answers.all():
        if answer.id_group not in to_ignore:
            data = {}
            homeworks = homework.answers.filter(id_group=answer.id_group)
            group = Groups.objects.get(id=homeworks[0].id_group)
            id_course = rg.course.id
            data['id_course'] = id_course
            data['name'] = group.name
            data['id_homework'] = homework.id
            data['answers'] = homeworks
            if data not in dic:
                dic.extend([data])
            to_ignore.append(answer.id_group)

    context = {
        'id_homework': id_homework,
        'dic': dic,
    }
    return render(request, "classmanagement/notation.html", context)


@login_required
def download_file(request):
    id = request.GET['id']
    id_homework = request.GET['id_homework']
    homework = Homework.objects.get(id=int(id_homework))
    rg = RequiredGroups.objects.get(id=homework.id_requiredgroup)
    if request.user not in rg.course.teacher.all():
        logger.warning(
            "User '" + request.user.username + "' denied to download'" + homework.name + "'.")
        raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
    answer = AnswerHomework.objects.get(id=id)
    filename = answer.file.name.split('/')[-1]
    response = HttpResponse(answer.file, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response


@login_required
def evaluate(request):
    id_answer = request.GET['id_answer']
    id_homework = request.GET['id_homework']
    homework = Homework.objects.get(id=id_homework)
    rg = RequiredGroups.objects.get(id=homework.id_requiredgroup)
    if request.user not in rg.course.teacher.all():
        logger.warning(
        "User '" + request.user.username + "' denied to evaluate'" + homework.name + "'.")
        raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
    grade = request.GET['grade']
    answer = AnswerHomework.objects.get(id=id_answer)
    answer.grade = grade
    answer.save()

    return redirect('/courses/course/notation/?id=' + id_homework)


@login_required
def remove_uploaded_file(request):
    id = request.GET['id']
    id_homework = request.GET['id_homework']
    homework = Homework.objects.get(id=id_homework)
    rg = RequiredGroups.objects.get(id=homework.id_requiredgroup)
    answer = AnswerHomework.objects.get(id=id)
    group = Groups.objects.get(id=answer.id_group)
    if request.user not in group.students.all():
        logger.warning(
            "User '" + request.user.username + "' denied for removing'" + answer.name + "'.")
        raise PermissionDenied("Vous n'êtes pas dans ce groupe.")
    homework.answers.remove(answer)
    homework.save()
    messages.success(request, "Le devoir a bien été supprimé")
    return redirect('/courses/course/homework/?id=' + id_homework)


@login_required
def download_all_file(request):
    id_homework = request.GET['id_homework']
    homework = Homework.objects.get(id=id_homework)
    rg = RequiredGroups.objects.get(id=homework.id_requiredgroup)
    if request.user not in rg.course.teacher.all():
        logger.warning(
        "User '" + request.user.username + "' denied download'" + homework.name + "'.")
        raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
    answer = homework.answers.all()
    print(answer)
    filenames = []
    for i in answer:
        print(i.file.name)
        filenames.append(i.file.url)
    # Files (local path) to put in the .zip
    # FIXME: Change this (get paths from DB etc)


    # Folder name in ZIP archive which contains the above files
    # E.g [thearchive.zip]/somefiles/file2.txt
    # FIXME: Set this to something better
    zip_subdir = "somefiles"
    zip_filename = "%s.zip" % zip_subdir

    # Open StringIO to grab in-memory ZIP contents
    s = StringIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        zip_path = os.path.join(zip_subdir, fname)

        # Add file, at correct path
        zf.write(fpath, zip_path)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(s.getvalue(), mimetype="application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp




