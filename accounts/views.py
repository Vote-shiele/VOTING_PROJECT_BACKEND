from django.forms import forms
from django.shortcuts import render, redirect
from .forms import AdminSignUpForm, AdminLoginForm, PollEditForm, PasswordVerificationForm, CandidateEditForm, \
    PollDeleteForm
from .models import Admin, AdminLog
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Q
from datetime import datetime
import qrcode
import io
import base64
from django.contrib import messages
from django.utils.timezone import now
from .models import VoteLog
from .forms import VoterForm
from .models import Poll, Candidate
from .forms import PollForm, CandidateForm
from django.shortcuts import get_object_or_404
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from io import BytesIO
import segno
from urllib.parse import urlencode
from django.shortcuts import render, redirect
from .forms import VoterValidationForm
from .models import Poll, Voter, Candidate, VoteLog
from django.db.models import Count

def signup_view(request):
    if request.method == 'POST':
        form = AdminSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_login')
    else:
        form = AdminSignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})
def login_view(request):
    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                admin = Admin.objects.get(username=username)
                if check_password(password, admin.password):
                    request.session['admin_id'] = admin.id
                    return redirect('admin_dashboard')
                else:
                    form.add_error(None, 'Invalid password')
            except Admin.DoesNotExist:
                form.add_error(None, 'Admin not found')
    else:
        form = AdminLoginForm()
    return render(request, 'accounts/login.html', {'form': form})
def admin_dashboard(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('admin_login')
    
    admin = get_object_or_404(Admin, id=admin_id)
    polls = Poll.objects.filter(admin=admin)
    return render(request, 'accounts/dashboard.html', {'admin': admin, 'polls': polls})
def create_poll(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('admin_login')

    if request.method == 'POST':
        form = PollForm(request.POST)
        if form.is_valid():
            poll = form.save(commit=False)
            poll.admin_id = admin_id
            poll.save()

            # Handle candidate creation if data is present
            candidate_names = request.POST.getlist('candidate_name')
            candidate_descriptions = request.POST.getlist('candidate_description')

            for name, description in zip(candidate_names, candidate_descriptions):
                if name:  # Only create if name is not empty
                    Candidate.objects.create(
                        poll=poll,
                        name=name,
                        description=description
                    )

            return redirect('poll_created', poll_id=poll.id)
    else:
        form = PollForm()

    return render(request, 'accounts/create_poll.html', {
        'form': form,
        'candidate_form': CandidateForm(),  # For the template
    })  #updated_Jun27_25
def add_candidate(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.poll = poll
            candidate.save()
            return redirect('admin_dashboard')
    else:
        form = CandidateForm()

    return render(request, 'accounts/add_candidate.html', {'form': form, 'poll': poll})
def add_voter(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.poll_type != 'private':
        return HttpResponse("You can only add voters to private polls.")

    if request.method == 'POST':
        form = VoterForm(request.POST)
        if form.is_valid():
            voter = form.save(commit=False)
            voter.poll = poll
            voter.save()
            # (You can send email here too)
            return redirect('admin_dashboard')
    else:
        form = VoterForm()

    return render(request, 'accounts/add_voter.html', {'form': form, 'poll': poll})
def admin_dashboard(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('admin_login')

    admin = get_object_or_404(Admin, id=admin_id)
    now = timezone.now()

    polls = Poll.objects.filter(admin=admin)
    ongoing_polls = polls.filter(end_date__gt=now)
    completed_polls = polls.filter(end_date__lte=now)

    return render(request, 'accounts/dashboard.html', {
        'admin': admin,
        'ongoing_polls': ongoing_polls,
        'completed_polls': completed_polls
    })
def settings_view(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('admin_login')

    admin = get_object_or_404(Admin, id=admin_id)

    return render(request, 'accounts/settings.html', {'admin': admin})
def poll_created_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.poll_type == 'public':
        # Generate QR code
        poll_url = request.build_absolute_uri(f'/poll/{poll.id}/validate/')

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(poll_url)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')

        # Convert to base64 for HTML
        buffered = io.BytesIO()
        img.save(buffered)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return render(request, 'accounts/poll_share.html', {
            'poll': poll,
            'poll_url': poll_url,
            'qr_code': img_str
        })
    else:
        # Private poll - show email invitation form
        return render(request, 'accounts/poll_invite.html', {'poll': poll})___
def send_invitations(request, poll_id):
    if request.method == 'POST':
        emails = request.POST.get('emails', '').split(',')
        poll = get_object_or_404(Poll, id=poll_id)

        for email in emails:
            if email.strip():
                send_mail(
                    f'Invitation to vote in {poll.name}',
                    f'You have been invited to vote in {poll.name}.',
                    'noreply@votingsystem.com',
                    [email.strip()],
                    fail_silently=False,
                )

        return redirect('admin_dashboard')

    return redirect('poll_created', poll_id=poll_id)
def search_polls(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return redirect('admin_login')

    admin = get_object_or_404(Admin, id=admin_id)
    query = request.GET.get('q', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    polls = Poll.objects.filter(admin=admin)

    if query:
        polls = polls.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query))

        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                polls = polls.filter(start_date__gte=start_date)
            except ValueError:
                pass

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            polls = polls.filter(end_date__lte=end_date)
        except ValueError:
            pass

    now = timezone.now()
    ongoing_polls = polls.filter(end_date__gt=now)
    completed_polls = polls.filter(end_date__lte=now)

    return render(request, 'accounts/search_results.html', {
        'admin': admin,
        'query': query,
        'start_date': start_date,
        'end_date': end_date,
        'ongoing_polls': ongoing_polls,
        'completed_polls': completed_polls,
        'active_tab': 'search'
    })
def poll_details(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    candidates = Candidate.objects.filter(poll=poll)

    # Generate voting portal URL
    base_url = request.build_absolute_uri('/').rstrip('/')
    voting_url = f"{base_url}/poll/{poll.id}/validate/"

    qr_code = get_qr_code(voting_url)

    return render(request, 'accounts/poll_details.html', {
        'poll': poll,
        'candidates': candidates,
        'qr_code': qr_code,
        'voting_url': voting_url,
        'now': timezone.now()
    })
def edit_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if request.method == 'POST':
        form = PollEditForm(request.POST, instance=poll)
        if form.is_valid():
            form.save()
            messages.success(request, 'Poll updated successfully!')
            return redirect('poll_details', poll_id=poll.id)
    else:
        form = PollEditForm(instance=poll)

    return render(request, 'accounts/edit_poll.html', {
        'form': form,
        'poll': poll,
    })
def vote_log(request, poll_id):
    if not request.session.get('admin_id'):
        return redirect('admin_login')

    poll = get_object_or_404(Poll, id=poll_id)
    votes = VoteLog.objects.filter(poll=poll).order_by('-voted_at')

    return render(request, 'accounts/vote_log.html', {
        'poll': poll,
        'votes': votes,
    })
def get_qr_code(url):
    """Generate a modern QR code with logo space"""
    buffered = BytesIO()

    # Create QR with center logo space
    qr = segno.make(url, error='h')
    qr.save(
        buffered,
        scale=6,
        kind='png',
        dark='#2563eb',  # Nice blue color
        light=None,  # Transparent background
        border=1,
        quiet_zone="#ffffff"  # White border
    )

    return base64.b64encode(buffered.getvalue()).decode()
def edit_candidate(request, candidate_id):
    """
    Secure candidate editing endpoint requiring:
    - Admin session authentication
    - Password reconfirmation
    - Audit logging
    """

    # Authentication check - redirects unauthenticated admins
    if not request.session.get('admin_id'):
        return redirect('admin_login')

    # Fetch required objects or 404
    candidate = get_object_or_404(Candidate, id=candidate_id)
    admin = get_object_or_404(Admin, id=request.session['admin_id'])

    # POST: Handle form submission
    if request.method == 'POST':
        password_form = PasswordVerificationForm(request.POST)
        candidate_form = CandidateEditForm(request.POST, request.FILES, instance=candidate)

        # Dual-form validation
        if password_form.is_valid() and candidate_form.is_valid():
            # Critical: Verify admin password matches
            if check_password(password_form.cleaned_data['password'], admin.password):
                # Save candidate changes
                candidate = candidate_form.save()

                # Create audit log entry
                AdminLog.objects.create(
                    admin=admin,
                    action='EDIT_CANDIDATE',  # Structured action type
                    details=f"Edited candidate_id={candidate.id} in poll_id={candidate.poll.id}",  # Context
                    ip_address=request.META.get('REMOTE_ADDR')  # Security logging
                )

                messages.success(request, 'Candidate updated successfully!')
                return redirect('poll_details', poll_id=candidate.poll.id)
            else:
                messages.error(request, 'Incorrect password')
    else:
        # GET: Initialize empty forms
        password_form = PasswordVerificationForm()
        candidate_form = CandidateEditForm(instance=candidate)

    return render(request, 'accounts/edit_candidate.html', {
        'candidate': candidate,  # For template context
        'candidate_form': candidate_form,  # Edit form
        'password_form': password_form,  # Security form
    })
def delete_poll(request, poll_id):
    """
    Admin endpoint for secure poll deletion with audit logging.
    Requires session auth, password confirmation, and admin privileges.
    """

    # Gate: Admin session check
    if not request.session.get('admin_id'):
        return redirect('admin_login')

    # Fetch protected resources
    poll = get_object_or_404(Poll, id=poll_id)
    admin = get_object_or_404(Admin, id=request.session['admin_id'])

    # POST: Handle deletion workflow
    if request.method == 'POST':
        form = PollDeleteForm(request.POST)
        if form.is_valid():
            # Security: Password + checkbox confirmation
            if form.cleaned_data['confirm'] and check_password(form.cleaned_data['password'], admin.password):

                # Audit trail before operation
                AdminLog.objects.create(
                    admin=admin,
                    action='DELETE_POLL',  # Structured action type
                    details=f"Deleted poll_id={poll.id} ({poll.name})",  # Contextual info
                    ip_address=request.META.get('REMOTE_ADDR')  # Forensic tracking
                )

                poll.delete()  # Cascades to related models
                messages.success(request, 'Poll deleted successfully!')
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Incorrect password or confirmation')
    else:
        form = PollDeleteForm()  # GET: Empty form

    return render(request, 'accounts/delete_poll.html', {
        'poll': poll,  # Context for confirmation UI
        'form': form,  # Password verification form
    })
def cast_vote(request, poll_id, candidate_id):
    """
    Processes a vote submission and broadcasts real-time updates.

    Returns JSON response with vote status and updated counts.
    """

    # Method validation - POST only endpoint
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    # Validate poll and candidate existence
    poll = get_object_or_404(Poll, id=poll_id)
    candidate = get_object_or_404(Candidate, id=candidate_id)

    # Voting window check
    if poll.end_date < now():
        return JsonResponse({'status': 'error', 'message': 'Voting period has ended'}, status=400)

    # Prevent duplicate voting for authenticated users
    if request.user.is_authenticated:
        if VoteLog.objects.filter(poll=poll, voter=request.user).exists():
            return JsonResponse({'status': 'error', 'message': 'You have already voted'}, status=400)

    # Record vote with IP tracking
    VoteLog.objects.create(
        poll=poll,
        voter=request.user if request.user.is_authenticated else None,  # Anonymous votes allowed
        candidate=candidate,
        ip_address=request.META.get('REMOTE_ADDR')  # Basic fraud prevention
    )

    # Calculate updated results
    votes = get_vote_counts(poll_id)
    total_votes = VoteLog.objects.filter(poll=poll).count()

    # Real-time update via WebSockets
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'votes_{poll_id}',  # Channel group name
        {
            'type': 'vote_update',  # Handler method name
            'total_votes': total_votes,
            'candidate_votes': votes
        }
    )

    return JsonResponse({
        'status': 'success',
        'total_votes': total_votes,  # Typo note: Should be 'total_votes'
        'candidate_votes': votes
    })
def get_vote_counts(poll_id):
    """
    Retrieves vote counts for all candidates in a specified poll.

    Args:
        poll_id: ID of the poll to retrieve results for

    Returns:
        Dict mapping candidate IDs to their name and vote count
        Format: {candidate_id: {'name': str, 'count': int}}

    Raises:
        Http404 if poll doesn't exist
    """
    # Fail fast if poll doesn't exist (returns 404)
    poll = get_object_or_404(Poll, id=poll_id)

    # Single query to get all candidates for this poll
    candidates = Candidate.objects.filter(poll=poll)
    votes = {}

    # Build results dictionary with one query per candidate
    for candidate in candidates:
        votes[candidate.id] = {
            'name': candidate.name,  # Candidate metadata
            'count': candidate.votelog_set.count()  # Reverse relation count
        }

    # Development logging - remove in production
    print(f"Vote counts: {votes}")

    return votes
def voter_validate(request, poll_id):
    # Pre-check: Validate poll existence before proceeding
    try:
        poll = Poll.objects.get(id=poll_id)
    except Poll.DoesNotExist:
        return render(request, 'accounts/error.html', {'message': 'Invalid Poll'})

    # Development convenience: Auto-create test voter
    # Note: Remove this block in production or implement proper environment checks
    if not Voter.objects.filter(username="johnsmith", email="johnsmith@gamil.com", poll=poll).exists():
        Voter.objects.create(
            username="johnsmith",
            email="johnsmith@gamil.com",
            password="test123",  # Security warning: Plaintext password
            poll=poll,
            has_voted=False
        )

    # Form processing for voter validation
    if request.method == 'POST':
        form = VoterValidationForm(request.POST)
        if form.is_valid():
            # Safe query pattern: Using filter().first() prevents exceptions
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            voter = Voter.objects.filter(
                username=username,
                email=email,
                poll=poll
            ).first()

            if not voter:
                # Non-field error for invalid credentials
                form.add_error(None, "Voter not found.")
            else:
                # Session setup for authenticated voting flow
                request.session['voter_id'] = voter.id
                request.session['validated_poll_id'] = poll_id
                return redirect(f'/poll/{poll_id}/vote/')
    else:
        form = VoterValidationForm()

    # Render validation form (GET) or invalid form (POST)
    return render(request, 'accounts/voter_validate.html', {
        'form': form,  # Form instance for template rendering
        'poll_id': poll_id  # Context for form action URL
    })
def vote_portal(request, poll_id):
    #  Authentication - Verify voter session and poll validation
    voter_id = request.session.get('voter_id')
    validated_poll_id = request.session.get('validated_poll_id')

    #  Security - Redirect unvalidated voters immediately
    if not voter_id or str(validated_poll_id) != str(poll_id):
        return redirect(f'/poll/{poll_id}/validate/')

    #  Voter-Poll Verification
    voter = Voter.objects.get(id=voter_id)

    # Optional but recommended: Extra poll-voter relationship check
    if str(voter.poll.id) != str(poll_id):
        return redirect(f'/poll/{poll_id}/validate/')

    poll = voter.poll
    candidates = Candidate.objects.filter(poll=poll)  # Get active candidates

    if request.method == 'POST':
        # Vote Processing
        candidate_id = request.POST.get('candidate_id')
        selected = Candidate.objects.get(id=candidate_id)

        #Persist vote (atomic create + voter status update)
        VoteLog.objects.create(poll=poll, voter=voter, candidate=selected)
        voter.has_voted = True  # Prevent duplicate voting
        voter.save()

        #Post-vote flow
        response = redirect(f'/poll/{poll_id}/results/')
        #Deferred session cleanup (after results view)
        request.session['clear_validation'] = True
        return response

    # GET Request: Show voting interface
    return render(request, 'accounts/vote_portal.html', {
        'poll': poll,
        'candidates': candidates  # Pass candidates for ballot display
    })
def results(request, poll_id):
    # Gate: Session-based voter auth with poll validation
    voter_id = request.session.get('voter_id')
    validated_poll_id = request.session.get('validated_poll_id')
    if not voter_id or str(validated_poll_id) != str(poll_id):
        return redirect(f'/poll/{poll_id}/validate/')  # Fail-fast to validation

    # Core data: Voter->Poll relationship assumed (1:1)
    voter = Voter.objects.get(id=voter_id)
    poll = voter.poll

    # Aggregation: Single-query pattern for totals + breakdown
    total_votes = VoteLog.objects.filter(poll=poll).count()
    candidate_votes = VoteLog.objects.filter(poll=poll
        ).values('candidate__name'
        ).annotate(votes=Count('id'))  # Note: Uses GROUP BY

    # Derived stat: Safe division for percentages
    for item in candidate_votes:
        item['percentage'] = round((item['votes'] / total_votes) * 100, 2) if total_votes > 0 else 0

    # Session cleanup: Conditional post-validation reset
    if request.session.get('clear_validation'):
        del request.session['validated_poll_id']  # Explicit invalidation
        del request.session['clear_validation']

    return render(request, 'accounts/results.html', {
        'poll': poll,  # Pass-through object
        'total_votes': total_votes,  # Pre-calculated metric
        'candidate_votes': candidate_votes,  # Annotated queryset
        'voter': voter,  # Contextual actor
    })
def clean(self):
    cleaned_data = super().clean()
    username = cleaned_data.get("username")
    email = cleaned_data.get("email")

    if not Voter.objects.filter(username=username, email=email).exists():
        raise forms.ValidationError("Voter not found or invalid credentials.")

    # ✅ Fix multiple objects error
    voter = Voter.objects.filter(username=username, email=email).first()

    if voter.has_voted:
        raise forms.ValidationError("This voter has already voted.")

    cleaned_data['voter'] = voter
    return cleaned_data
