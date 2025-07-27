from django.contrib import admin
from .models import Admin, Poll, Candidate, Voter, AdminLog, VoteLog

# Register custom user/admin model so it appears in Django admin UI
admin.site.register(Admin)

# Register Poll model for creating/editing/deleting polls via the admin interface
admin.site.register(Poll)

# Register Candidate model to manage poll candidates from admin
admin.site.register(Candidate)

# Register Voter model to allow admins to view, add, or remove eligible voters
admin.site.register(Voter)

# Register VoteLog to audit all submitted votes (who voted for whom)
admin.site.register(VoteLog)

# Register AdminLog to track admin actions (e.g. logins, changes) if implemented
admin.site.register(AdminLog)
