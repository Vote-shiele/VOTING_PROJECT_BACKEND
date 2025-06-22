from django.urls import path
from . import views

urlpatterns = [
    path('', views.signup_view, name='admin_signup'),
    path('login/', views.login_view, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('settings/', views.settings_view, name='admin_settings'),
    path('create-poll/', views.create_poll, name='create_poll'),
    path('poll-created/<int:poll_id>/', views.poll_created_view, name='poll_created'),
    path('send-invitations/<int:poll_id>/', views.send_invitations, name='send_invitations'),
    path('add-candidate/<int:poll_id>/', views.add_candidate, name='add_candidate'),
    path('add-voter/<int:poll_id>/', views.add_voter, name='add_voter'),
    path('search/', views.search_polls, name='search_polls'),
]