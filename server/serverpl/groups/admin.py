from django.contrib import admin
from groups.models import Groups, RequiredGroups


@admin.register(Groups)
class GroupsAdmin(admin.ModelAdmin):
    list_display=('__str__', 'creation_date')

@admin.register(RequiredGroups)
class RequiredGroupsAdmin(admin.ModelAdmin):
    list_display=('__str__', 'course', 'limit_date')
