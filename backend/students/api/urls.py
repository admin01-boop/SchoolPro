from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('students', views.StudentViewSet)
router.register('guardians', views.GuardianViewSet)
router.register('student-guardians', views.StudentGuardianViewSet)
router.register('emergency-contacts', views.EmergencyContactViewSet)
router.register('enrollments', views.EnrollmentViewSet)
router.register('roster-teachers', views.RosterTeacherViewSet, basename='roster-teachers')
router.register('roster-staff', views.RosterStaffViewSet, basename='roster-staff')
router.register('roster-observers', views.RosterObserverViewSet, basename='roster-observers')
router.register('roster-admins', views.RosterAdminViewSet, basename='roster-admins')
router.register('roster-parents', views.RosterParentViewSet, basename='roster-parents')

urlpatterns = [
    path('roster-filter-options/', views.RosterFilterOptionsView.as_view()),
    path('roster-user-options/', views.RosterUserOptionsView.as_view()),
    path('roster-users/', views.RosterUserCreateView.as_view()),
    path('me/student/', views.MyStudentView.as_view()),
    path('me/children/', views.MyChildrenView.as_view()),
] + router.urls
