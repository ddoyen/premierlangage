 # coding: utf-8
 
from django.urls import path
from django.conf.urls import url
from django.contrib.auth import views as auth_views



from classmanagement import views

app_name = 'classmanagement'

urlpatterns = [
    url(r'^course/(\d+)/$', views.course_view),
    url(r'^course/upload/$', views.upload_file),
    url(r'^course/upload_grade/$', views.upload_grade),
    url(r'^course/evaluate/$', views.evaluate),
    url(r'^course/subject/$', views.get_subject),
    url(r'^course/remove_uploaded/$', views.remove_uploaded_file),
    url(r'^course/download/$', views.download_file),
    url(r'^course/download_all/$', views.download_all_file),
    url(r'^course/notation/$', views.notation),
    url(r'^course/(\d+)/$', views.course_view, name="course"),
    url(r'^course/(\d+)/student/(\d+)/summary/$', views.student_summary),
    url(r'^course/(\d+)/(\w+)/summary/$', views.activity_summary),
    url(r'^course/(\d+)/summary/$', views.course_summary),
    url(r'^course/homework/$', views.homework_summary),
    url(r'^redirect/(\d+)/$', views.redirect_activity),
    url(r'^logout/$', views.disconnect, name="logout"),
    path('login/', auth_views.LoginView.as_view(template_name='playexo/not_authenticated.html', redirect_authenticated_user=True), name="login"),
]

