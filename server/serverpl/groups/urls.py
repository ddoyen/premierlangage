from django.conf.urls import url
from groups import views

app_name = 'groups'

urlpatterns = [
    url(r'^$', views.index),
    url(r'^group/$', views.show_groups),
    url(r'^group/joingroup/$', views.join_group),
    url(r'^group/joingroup_admin/$', views.join_group_admin),
    url(r'^group/leavegroup/$', views.leave_group),
    url(r'^group/creategroup/$', views.create_new_group),
    url(r'^group/kick/$', views.kick_from_group),
    url(r'^group/rename/$', views.rename_group),
    url(r'^group/auto_rename/$', views.auto_rename_group),
    url(r'^group/remove/$', views.remove_group),
    url(r'^group/resize/$', views.remove_group),
    url(r'^group/creategroup_admin/$', views.create_new_group_admin),
    url(r'^group/auto_create/$', views.auto_create_group),
    url(r'^group/auto_fill/$', views.auto_fill_group),
]