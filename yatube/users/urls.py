from django.contrib.auth import views as extra_views
from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignUp.as_view(), name='signup'),
    path(
        'logout/',
        extra_views.LogoutView.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'login/',
        extra_views.LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'password_reset/',
        extra_views.PasswordResetView.as_view(
            template_name='users/password_reset_form.html'
        ),
        name='password_reset_form'
    ),
    path(
        'password_change/',
        extra_views.PasswordChangeView.as_view(
            template_name='users/password_change_form.html'
        ),
        name='password_change_form'
    ),
    path(
        'reset/<slug:uidb64>/<slug:token>/',
        extra_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),
]
