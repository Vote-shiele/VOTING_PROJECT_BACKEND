from django.contrib import admin
from .models import Admin, Poll, Candidate, Voter, AdminLog
from .models import VoteLog


admin.site.register(Admin)
admin.site.register(Poll)
admin.site.register(Candidate)
admin.site.register(Voter)
admin.site.register(VoteLog)
admin.site.register(AdminLog)


