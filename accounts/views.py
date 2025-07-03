from django.shortcuts import render, redirect
from .forms import AdminSignUpForm, AdminLoginForm, PollEditForm, PasswordVerificationForm, CandidateEditForm, \
    PollDeleteForm
from .models import Admin, AdminLog
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
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
    qr_code = get_qr_code(request.build_absolute_uri(f'/poll-details/{poll.id}/'))
    return render(request, 'accounts/poll_details.html', {
        'poll': poll,
        'candidates': candidates,
        'qr_code': qr_code,
        'now': timezone.now()
    }) #updated_Jun27_25
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
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffered = io.BytesIO()
    img.save(buffered)
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


from django.views.decorators.http import require_GET, require_POST


@require_GET
def voter_portal(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    candidates = poll.candidate_set.all()

    # Verify voter access for private polls
    if poll.poll_type == 'private' and not request.session.get(f'voter_{poll_id}'):
        return HttpResponseForbidden("You must be invited to access this poll")

    return render(request, 'voter_templates/vote_portal.html', {
        'poll': poll,
        'candidates': candidates,
        'now': timezone.now()
    })


@require_POST
def submit_vote(request):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    candidate_id = request.POST.get('candidate_id')
    poll_id = request.POST.get('poll_id')

    # Validate vote
    candidate = get_object_or_404(Candidate, id=candidate_id, poll_id=poll_id)
    poll = candidate.poll

    # Check voting window
    if not (poll.start_date <= timezone.now() <= poll.end_date):
        return JsonResponse({'error': 'Voting period closed'}, status=403)

    # Record vote (with IP for fraud detection)
    VoteLog.objects.create(
        candidate=candidate,
        voter=request.user if request.user.is_authenticated else None,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return JsonResponse({
        'success': True,
        'new_count': candidate.votelog_set.count()
    })