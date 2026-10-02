from django.contrib import admin

from .models import AdminProfile, Observer, StaffMember, Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'hire_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'job_title', 'department')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id', 'department')


@admin.register(Observer)
class ObserverAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'organization')


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'job_title', 'phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')
