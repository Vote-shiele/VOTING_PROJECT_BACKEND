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
# poll sharing functionality
def poll_created_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.poll_type == 'public':
        # Generate QR code
        poll_url = request.build_absolute_uri(f'/poll/{poll.id}/')
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
        return render(request, 'accounts/poll_invite.html', {'poll': poll})
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
    voting_url = f"{base_url}/poll/{poll.id}/portal/"

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

#updated_Jun27_25
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
    if not request.session.get('admin_id'):
        return redirect('admin_login')

    candidate = get_object_or_404(Candidate, id=candidate_id)
    admin = get_object_or_404(Admin, id=request.session['admin_id'])

    if request.method == 'POST':
        password_form = PasswordVerificationForm(request.POST)
        candidate_form = CandidateEditForm(request.POST, request.FILES, instance=candidate)

        if password_form.is_valid() and candidate_form.is_valid():
            if check_password(password_form.cleaned_data['password'], admin.password):
                candidate = candidate_form.save()

                # Log the action
                AdminLog.objects.create(
                    admin=admin,
                    action='EDIT_CANDIDATE',
                    details=f"Edited candidate_id={candidate.id} in poll_id={candidate.poll.id}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )

                messages.success(request, 'Candidate updated successfully!')
                return redirect('poll_details', poll_id=candidate.poll.id)
            else:
                messages.error(request, 'Incorrect password')
    else:
        password_form = PasswordVerificationForm()
        candidate_form = CandidateEditForm(instance=candidate)

    return render(request, 'accounts/edit_candidate.html', {
        'candidate': candidate,
        'candidate_form': candidate_form,
        'password_form': password_form,
    })
def delete_poll(request, poll_id):
    if not request.session.get('admin_id'):
        return redirect('admin_login')

    poll = get_object_or_404(Poll, id=poll_id)
    admin = get_object_or_404(Admin, id=request.session['admin_id'])

    if request.method == 'POST':
        form = PollDeleteForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['confirm'] and check_password(form.cleaned_data['password'], admin.password):
                # Log the action before deletion
                AdminLog.objects.create(
                    admin=admin,
                    action='DELETE_POLL',
                    details=f"Deleted poll_id={poll.id} ({poll.name})",
                    ip_address=request.META.get('REMOTE_ADDR')
                )

                poll.delete()
                messages.success(request, 'Poll deleted successfully!')
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Incorrect password or confirmation')
    else:
        form = PollDeleteForm()

    return render(request, 'accounts/delete_poll.html', {
        'poll': poll,
        'form': form,
    })


def voting_portal(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    candidates = Candidate.objects.filter(poll=poll).select_related('poll').prefetch_related('votelog_set')

    # Calculate time remaining
    time_remaining = "Poll ended"
    if poll.end_date > now():
        delta = poll.end_date - now()
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        time_remaining = f"{days}d {hours}h {minutes}m"

    # Prepare candidates data
    candidates_data = []
    total_votes = 0

    for candidate in candidates:
        vote_count = candidate.votelog_set.count()
        total_votes += vote_count

        candidates_data.append({
            'id': candidate.id,
            'name': candidate.name,
            'description': candidate.description,
            'description_points': candidate.description.split('\n') if candidate.description else [],
            'vote_count': vote_count,
            'image': candidate.image
        })

    # Determine which base template to use
    if request.GET.get('admin'):  # Optional flag for admin view
        base_template = 'accounts/base.html'
    else:
        base_template = 'accounts/base_voter.html'

    return render(request, 'accounts/voting_portal.html', {
        'poll': poll,
        'candidates': candidates_data,
        'time_remaining': time_remaining,
        'total_votes': total_votes,
        'now': now(),
        'base_template': base_template  # Pass to template if needed
    })

def cast_vote(request, poll_id, candidate_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    poll = get_object_or_404(Poll, id=poll_id)
    candidate = get_object_or_404(Candidate, id=candidate_id)

    # Check if poll is still active
    if poll.end_date < now():
        return JsonResponse({'status': 'error', 'message': 'Voting period has ended'}, status=400)

    # Check if user already voted (if authenticated)
    if request.user.is_authenticated:
        if VoteLog.objects.filter(poll=poll, voter=request.user).exists():
            return JsonResponse({'status': 'error', 'message': 'You have already voted'}, status=400)

    # Create vote log
    VoteLog.objects.create(
        poll=poll,
        voter=request.user if request.user.is_authenticated else None,
        candidate=candidate,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    # Get updated vote counts
    votes = get_vote_counts(poll_id)
    total_votes = VoteLog.objects.filter(poll=poll).count()

    # Broadcast update to all connected clients
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'votes_{poll_id}',
        {
            'type': 'vote_update',
            'total_votes': total_votes,
            'candidate_votes': votes
        }
    )

    return JsonResponse({
        'status': 'success',
        'total_votes': total_votes,
        'candidate_votes': votes
    })


def get_vote_counts(poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    candidates = Candidate.objects.filter(poll=poll)
    votes = {}

    for candidate in candidates:
        votes[candidate.id] = {
            'name': candidate.name,
            'count': candidate.votelog_set.count()
        }
    print(f"Vote counts: {votes}")
    return votes
