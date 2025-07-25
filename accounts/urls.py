from django.urls import path
from . import views
from .views import cast_vote

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
    path('poll-details/<int:poll_id>/', views.poll_details, name='poll_details'),
    path('edit-poll/<int:poll_id>/', views.edit_poll, name='edit_poll'),
    path('vote-log/<int:poll_id>/', views.vote_log, name='vote_log'),
    path('edit-candidate/<int:candidate_id>/', views.edit_candidate, name='edit_candidate'),
    path('delete-poll/<int:poll_id>/', views.delete_poll, name='delete_poll'),
    path('poll/<int:poll_id>/vote/<int:candidate_id>/', cast_vote, name='cast_vote'),
    #path('poll/<int:poll_id>/portal/', views.voting_portal, name='voting_portal'),
    path('poll/<int:poll_id>/validate/', views.voter_validate, name='voter_validate'),
    path('poll/<int:poll_id>/vote/', views.vote_portal, name='vote_portal'),
    path('poll/<int:poll_id>/results/', views.results, name='results'),

]