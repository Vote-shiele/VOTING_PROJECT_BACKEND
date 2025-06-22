from django.contrib import admin
from .models import Admin, Poll, Candidate,Voter

admin.site.register(Admin)
admin.site.register(Poll)
admin.site.register(Candidate)
admin.site.register(Voter)


