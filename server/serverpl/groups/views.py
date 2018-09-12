from groups.models import Groups, RequiredGroups
from datetime import datetime, timezone
import random
import logging
from django.http import HttpResponseNotAllowed, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect

logger = logging.getLogger(__name__)


def is_in_group(required_group, user):
    for group in required_group.groups.all():
        if user in group.students.all():
            return True
    return False


@login_required
@csrf_exempt
def index(request):
    required_groups = RequiredGroups.objects.all()
    cpt = 0
    today = datetime.now(timezone.utc)
    teacher = False
    for rg in required_groups:
        if is_teacher(request, rg):
            teacher = True
        limit = rg.limit_date
        rg.state = limit > today
        if request.user in rg.course.student.all():
            cpt = cpt + 1

    return render(request, 'groups/index.html', {
        'is_teacher': teacher,
        'required_groups': required_groups,
        'nb_group': cpt,
        'today': today,
    })

@login_required
@csrf_exempt
def show_groups(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        id = request.GET['id']
        if not id:
            return HttpResponseBadRequest("Missing 'id' parameter")
        today = datetime.now(timezone.utc)
        required_groups = RequiredGroups.objects.get(id=id)
        groups = required_groups.groups.all()
        in_group = False
        limit = required_groups.limit_date
        state = limit > today
        for i in range(0, len(groups)):
            if request.user in groups[i].students.all():
                in_group = True
            if groups[i].password == "":
                groups[i].need_password = False
            else:
                groups[i].need_password = True
            groups[i].avalaible_spot = list(range(groups[i].max_members - len(groups[i].students.all())))
            groups[i].avalaible_spot2 = groups[i].max_members - len(groups[i].students.all())
        available_student = []
        for member in required_groups.course.student.all():
            if not is_in_group(required_groups, member):
                available_student.append(member)
        context = {
            'available_student': available_student,
            'id_required_groups': id,
            'id_course': required_groups.course.id,
            'max_members': required_groups.max_members,
            'groups': groups,
            'in_group' : in_group,
            'state' : state,
            'is_teacher': is_teacher(request, required_groups),
        }
    except RequiredGroups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
        return redirect('/groups/')
    return render(request, "groups/group.html", context)


def is_teacher(request, required_groups):
    if request.user in required_groups.course.teacher.all():
        return True
    return False


def new_name(lst):
    students = []
    for student in lst:
        students.append(student.username)
    name = '_'.join(students)
    return name

@login_required
@csrf_exempt
def join_group(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try :
        id = request.GET['id']
        if not id:
            return HttpResponseBadRequest("Missing 'id' parameter")
        id_required_groups = request.GET['id_required_groups']
        if not id_required_groups:
            return HttpResponseBadRequest("Missing 'id_required_groups' parameter")
        try:
            group = Groups.objects.get(id=id)
        except:
            raise Http404("Group (id: " + str(id) + ") not found.")
        if len(group.students.all()) == group.max_members:
            messages.error(request, "Le groupe " + group.name + " est complet.")
            return redirect('/groups/group/?id=' + id_required_groups)
        if request.user in group.students.all():
            messages.error(request, "Vous êtes déjà dans le groupe " + group.name + ".")
            return redirect('/groups/group/?id=' + id_required_groups)
        password = request.GET['password']
        if password != group.password:
            messages.error(request, "Mauvais mot de passe pour rejoindre le groupe " + group.name + ".")
            return redirect('/groups/group/?id=' + id_required_groups)
        group.students.add(request.user)
        group.name = new_name(group.students.all())
        group.save()
        messages.success(request, "Vous avez rejoint le groupe " + group.name + ".")
    except Groups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
    return redirect('/groups/group/?id=' +id_required_groups)



@login_required
@csrf_exempt
def leave_group(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try :
        id_required_groups = request.GET['id_required_groups']
        if not id_required_groups:
            return HttpResponseBadRequest("Missing 'id_required_groups' parameter")
        id = request.GET['id']
        if not id:
            return HttpResponseBadRequest("Missing 'id' parameter")
        try:
            group = Groups.objects.get(id=id)
        except:
            raise Http404("Group (id: " + str(id) + ") not found.")
        if request.user not in group.students.all():
            messages.error(request, "Vous n'êtes pas dans le groupe " + group.name +
                           ", impossible de le quitter.")
            return redirect('/groups/group/?id=' + id_required_groups)
        group.students.remove(request.user)
        if len(group.students.all()) < 1:
            Groups.objects.filter(id=id).delete()
            messages.success(request, "Vous avez quitté le groupe " + group.name + " et le groupe a été supprimé.")
        else:
            messages.success(request, "Vous avez quitté le groupe " + group.name + ".")
            group.name = new_name(group.students.all())
        group.save()
    except Groups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
    return redirect('/groups/group/?id=' + id_required_groups)


@login_required
@csrf_exempt
def create_new_group(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        id_required_groups = request.GET['id_required_groups']
        if not id_required_groups:
            return HttpResponseBadRequest("Missing 'id_required_groups' parameter")
        max_members = request.GET['max_members']
        if not max_members:
            return HttpResponseBadRequest("Missing 'max_members' parameter")
        password = request.GET['password']
        g = Groups(name=request.user.username, max_members=max_members, creation_date=datetime.now(),
                   password=password)
        g.save()
        g.students.add(request.user)
        try:
            rg = RequiredGroups.objects.get(id=id_required_groups)
        except:
            raise Http404("RequiredGroups (id: " + str(id_required_groups) + ") not found.")
        rg.groups.add(g)
    except RequiredGroups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
        return redirect('/groups/')
    return redirect('/groups/group/?id=' + id_required_groups)


@login_required
@csrf_exempt
def kick_from_group(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        id_required_groups = request.GET['id_required_groups']
        if not id_required_groups:
            return HttpResponseBadRequest("Missing 'id_required_groups' parameter")
        try:
            required_groups = RequiredGroups.objects.get(id=id_required_groups)
        except:
            raise Http404("RequiredGroups (id: " + str(id_required_groups) + ") not found.")
        if not is_teacher(request, required_groups):
            logger.warning(
                "User '" + request.user.username + "' denied to use the auto creation'" + "'.")
            raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
        id = request.GET['id']
        id_student = request.GET['id_student']
        if not id_student:
            return HttpResponseBadRequest("Missing 'id_student' parameter")
        try:
            user = User.objects.get(id=id_student)
        except:
            raise Http404("User (id: " + str(id_student) + ") not found.")
        try:
            group = Groups.objects.get(id=id)
        except:
            raise Http404("Groups (id: " + str(id) + ") not found.")
        group.students.remove(user)
        messages.success(request,
                         "L'étudiant " + user.username + " a été expulsé du groupe " + group.name + ".")
        group.name = new_name(group.students.all())
        group.save()
    except RequiredGroups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
        return redirect('/groups/')
    except User.DoesNotExist:
        messages.error(request, "L'utilisateur n'existe pas")
        return redirect('/groups/group/?id=' + id_required_groups)
    except Groups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
        return redirect('/groups/group/?id=' + id_required_groups)
    return redirect('/groups/group/?id=' + id_required_groups)


@login_required
@csrf_exempt
def remove_group(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        id_required_groups = request.GET['id_required_groups']
        if not id_required_groups:
            return HttpResponseBadRequest("Missing 'id_required_groups' parameter")
        try:
            required_groups = RequiredGroups.objects.get(id=id_required_groups)
        except:
            raise Http404("RequiredGroups (id: " + str(id_required_groups) + ") not found.")
        id = request.GET['id']
        if not id:
            return HttpResponseBadRequest("Missing 'id' parameter")
        if not is_teacher(request, required_groups):
            logger.warning(
                "User '" + request.user.username + "' denied to use the auto creation'" + "'.")
            raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
        try:
            group = Groups.objects.get(id=id)
        except:
            raise Http404("Groups (id: " + str(id) + ") not found.")
        required_groups.groups.remove(group)
        messages.success(request, "Le groupe " + group.name + " a été supprimé.")
        required_groups.save()
        return redirect('/groups/group/?id=' + id_required_groups)
    except RequiredGroups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
        return redirect('/groups/')
    except Groups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
        return redirect('/groups/group/?id=' + id_required_groups)


@login_required
@csrf_exempt
def create_new_group_admin(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try:
        id_required_groups = request.GET['id_required_groups']
        if not id_required_groups:
            return HttpResponseBadRequest("Missing 'id_required_groups' parameter")
        max_members = request.GET['max_members']
        if not max_members:
            return HttpResponseBadRequest("Missing 'max_members' parameter")
        name = request.GET['name']
        if not name:
            return HttpResponseBadRequest("Missing 'name' parameter")
        password = request.GET['password']
        if not password and password != '':
            return HttpResponseBadRequest("Missing 'password' parameter")
        if int(max_members) > 99:
            messages.error(request, "Le groupe est trop grand")
            return redirect('/groups/group/?id=' + id_required_groups)
        try:
            rg = RequiredGroups.objects.get(id=id_required_groups)
        except:
            raise Http404("RequiredGroups (id: " + str(id_required_groups) + ") not found.")
        if not is_teacher(request, rg):
            logger.warning(
                "User '" + request.user.username + "' denied to use the auto creation'" + "'.")
            raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
        g = Groups(name=name, max_members=max_members, creation_date=datetime.now(),
                   password=password)
        g.save()
        rg.groups.add(g)
    except RequiredGroups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
        return redirect('/groups/')
    messages.success(request, "Le groupe " + g.name + " a bien été créé")
    return redirect('/groups/group/?id=' + id_required_groups)


@login_required
@csrf_exempt
def join_group_admin(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try :
        id = request.GET['id']
        if not id:
            return HttpResponseBadRequest("Missing 'id' parameter")
        id_user = request.GET['id_user']
        if not id_user:
            return HttpResponseBadRequest("Missing 'id_user' parameter")
        id_required_groups = request.GET['id_required_groups']
        if not id_required_groups:
            return HttpResponseBadRequest("Missing 'id_required_groups' parameter")
        try:
            rg = RequiredGroups.objects.get(id=id_required_groups)
        except:
            raise Http404("RequiredGroups (id: " + str(id_required_groups) + ") not found.")
        if not is_teacher(request, rg):
            logger.warning(
                "User '" + request.user.username + "' denied to use the auto creation'" + "'.")
            raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
        try:
            group = Groups.objects.get(id=id)
        except:
            raise Http404("Groups (id: " + str(id) + ") not found.")
        try:
            user = User.objects.get(id=id_user)
        except:
            raise Http404("User (id: " + str(id_user) + ") not found.")
        if len(group.students.all()) >= group.max_members:
            messages.error(request, "Le groupe " + group.name + " est complet.")
            return redirect('/groups/group/?id=' + id_required_groups)
        if user in group.students.all():
            messages.error(request, user.username + " est déjà dans le groupe " + group.name + ".")
            return redirect('/groups/group/?id=' + id_required_groups)
        group.students.add(user)
        group.save()
        messages.success(request, user.username + " a rejoint le groupe " + group.name + ".")
    except Groups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
    except User.DoesNotExist:
        messages.error(request, "L'utilisateur n'existe pas")
    return redirect('/groups/group/?id=' +id_required_groups)


@login_required
@csrf_exempt
def rename_group(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try :
        id = request.GET['id']
        name = request.GET['name']
        id_required_groups = request.GET['id_required_groups']
        try:
            rg = RequiredGroups.objects.get(id=id_required_groups)
        except:
            raise Http404("RequiredGroups (id: " + str(id_required_groups) + ") not found.")
        if not is_teacher(request, rg):
            logger.warning(
                "User '" + request.user.username + "' denied to use the auto creation'" + "'.")
            raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
        try:
            group = Groups.objects.get(id=id)
        except:
            raise Http404("Groups (id: " + str(id) + ") not found.")
        group.name = name
        group.save()
        messages.success(request, "Le groupe a bien été renommé en " + group.name + ".")
    except Groups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
    return redirect('/groups/group/?id=' + id_required_groups)


@login_required
@csrf_exempt
def auto_rename_group(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try :
        id = request.GET['id']
        if not id:
            return HttpResponseBadRequest("Missing 'id' parameter")
        id_required_groups = request.GET['id_required_groups']
        if not id_required_groups:
            return HttpResponseBadRequest("Missing 'id_required_groups' parameter")
        try:
            rg = RequiredGroups.objects.get(id=id_required_groups)
        except:
            raise Http404("RequiredGroups (id: " + str(id_required_groups) + ") not found.")
        if not is_teacher(request, rg):
            logger.warning(
                "User '" + request.user.username + "' denied to use the auto creation'" + "'.")
            raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
        try:
            group = Groups.objects.get(id=id)
        except:
            raise Http404("Groups (id: " + str(id) + ") not found.")
        if len(group.students.all()) < 1:
            messages.error(request, "Le groupe est vide !")
            return redirect('/groups/group/?id=' + id_required_groups)
        group.name = new_name(group.students.all())
        group.save()
        messages.success(request, "Le groupe a bien été renommé en " + group.name + ".")
    except Groups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
    return redirect('/groups/group/?id=' + id_required_groups)


@login_required
@csrf_exempt
def resize_group(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try :
        id = request.GET['id']
        if not id:
            return HttpResponseBadRequest("Missing 'id' parameter")
        max_members = request.GET['max_members']
        if not max_members:
            return HttpResponseBadRequest("Missing 'max_members' parameter")
        id_required_groups = request.GET['id_required_groups']
        if not id_required_groups:
            return HttpResponseBadRequest("Missing 'id_required_groups' parameter")
        try:
            rg = RequiredGroups.objects.get(id=id_required_groups)
        except:
            raise Http404("RequiredGroups (id: " + str(id_required_groups) + ") not found.")
        if not is_teacher(request, rg):
            logger.warning(
                "User '" + request.user.username + "' denied to use the auto creation'" + "'.")
            raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
        try:
            group = Groups.objects.get(id=id)
        except:
            raise Http404("Groups (id: " + str(id) + ") not found.")
        group.max_members = max_members
        group.save()
        messages.success(request, "Vous avez rejoint le groupe " + group.name + ".")
    except Groups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")



@login_required
@csrf_exempt
def auto_fill_group(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try :
        id_required_groups = request.GET['id_required_groups']
        if not id:
            return HttpResponseBadRequest("Missing 'id-required_group' parameter")
        try:
            rg = RequiredGroups.objects.get(id=id_required_groups)
        except:
            raise Http404("RequiredGroups (id: " + str(id_required_groups) + ") not found.")
        if not is_teacher(request, rg):
            logger.warning(
                "User '" + request.user.username + "' denied to use the auto creation'" + "'.")
            raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
        remaining_student = []
        for student in rg.course.student.all():
            remaining_student.append(student)

        for group in rg.groups.all():
            for student in group.students.all():
                remaining_student.remove(student)

        if len(remaining_student) < 1:
            messages.success(request, "Il n'y a pas d'étudiant sans groupe")
            return redirect('/groups/group/?id=' + id_required_groups)


        for group in rg.groups.all():
            if len(remaining_student) < 1:
                break
            while len(group.students.all()) < rg.max_members and len(remaining_student) > 0:
                student = random.choice(remaining_student)
                group.students.add(student)
                remaining_student.remove(student)
                group.name = new_name(group.students.all())
                group.save()



        remaining_group = []
        for group in rg.groups.all():
            if len(group.students.all()) != rg.max_members:
                remaining_group.append(group)
                remaining_student.extend(group.students.all())

        for group in remaining_group:
            rg.groups.remove(group)

        while len(remaining_student) > 0:
            g = Groups(name='test', max_members=rg.max_members, password='')
            g.save()
            for i in range(rg.max_members):
                if len(remaining_student) < 1:
                    break
                student = random.choice(remaining_student)
                g.students.add(student)
                remaining_student.remove(student)
                g.name = new_name(g.students.all())
                g.save()
            rg.groups.add(g)

        rg.save()

    except Groups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
        return redirect('/groups/')
    messages.success(request, "Les groupes ont bien été complété")
    return redirect('/groups/group/?id=' + id_required_groups)


@login_required
@csrf_exempt
def auto_create_group(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    try :
        id_required_groups = request.GET['id_required_groups']
        if not id_required_groups:
            return HttpResponseBadRequest("Missing 'id_required_groups' parameter")
        try:
            rg = RequiredGroups.objects.get(id=id_required_groups)
        except:
            raise Http404("RequiredGroups (id: " + str(id_required_groups) + ") not found.")
        if not is_teacher(request, rg):
            logger.warning(
                "User '" + request.user.username + "' denied to use the auto creation'" + "'.")
            raise PermissionDenied("Vous n'êtes pas professeur de cette classe.")
        remaining_student = []
        for student in rg.course.student.all():
            remaining_student.append(student)


        for group in rg.groups.all():
           rg.groups.remove(group)
        rg.save()

        while len(remaining_student) > 0:
            g = Groups(name='test', max_members=rg.max_members, password='')
            g.save()
            for i in range(rg.max_members):
                if len(remaining_student) < 1:
                    break
                student = random.choice(remaining_student)
                g.students.add(student)
                remaining_student.remove(student)
                g.name = new_name(g.students.all())
                g.save()
            rg.groups.add(g)
        rg.save()

    except Groups.DoesNotExist:
        messages.error(request, "Le groupe n'existe pas")
        return redirect('/groups/')
    messages.success(request, "Les groupes ont été créé de manière aléatoire")
    return redirect('/groups/group/?id=' + id_required_groups)