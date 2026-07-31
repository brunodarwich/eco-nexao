from django.urls import path

from .views import CsrfTokenView, LoginView, LogoutView, SessionView

urlpatterns = [
    path("csrf", CsrfTokenView.as_view(), name="admin-auth-csrf"),
    path("login", LoginView.as_view(), name="admin-auth-login"),
    path("session", SessionView.as_view(), name="admin-auth-session"),
    path("logout", LogoutView.as_view(), name="admin-auth-logout"),
]
