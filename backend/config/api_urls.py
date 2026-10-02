"""Routes mounted under /api/v1/."""
from django.urls import include, path

from accounts.views import ChangePasswordView, LoginView, LogoutView

urlpatterns = [
    path('auth-token/', LoginView.as_view()),
    path('auth/logout/', LogoutView.as_view()),
    path('auth/change-password/', ChangePasswordView.as_view()),
    path('', include('academics.api.urls')),
    path('', include('students.api.urls')),
]
