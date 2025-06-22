from django.shortcuts import render, redirect
from .forms import AdminSignUpForm, AdminLoginForm
from .models import Admin
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.http import HttpResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db.models import Q
from datetime import datetime
import qrcode
import io
import base64

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

from .models import Poll, Candidate
from .forms import PollForm, CandidateForm
from django.shortcuts import get_object_or_404

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
            return redirect('poll_created', poll_id=poll.id)
    else:
        form = PollForm()

    return render(request, 'accounts/create_poll.html', {'form': form})


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

from .forms import VoterForm

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