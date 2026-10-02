from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('academic-years', views.AcademicYearViewSet)
router.register('curriculums', views.CurriculumViewSet)
router.register('programmes', views.ProgrammeViewSet)
router.register('grade-levels', views.GradeLevelViewSet)
router.register('classrooms', views.ClassRoomViewSet)
router.register('lead-sources', views.LeadSourceViewSet)

urlpatterns = [
    path('key-academic-functions/', views.KeyAcademicFunctionsView.as_view()),
    path('years-levels-grid/', views.YearsLevelsGridView.as_view()),
] + router.urls
